# Prototype vein mask on the swatch: iso-contours of strongly domain-warped fBm.
import bpy, sys
argv=sys.argv[sys.argv.index("--")+1:]
m=bpy.data.materials["Marble"]; nt=m.node_tree; N=nt.nodes; L=nt.links; N.clear()
def node(t,**kw):
    x=N.new(t)
    for k,v in kw.items(): setattr(x,k,v)
    return x
def math(op,a,b=None):
    x=node('ShaderNodeMath',operation=op)
    for i,v in enumerate((a,b)):
        if v is None: continue
        if isinstance(v,(int,float)): x.inputs[i].default_value=v
        else: L.new(v,x.inputs[i])
    return x.outputs[0]
def vm(op,a,b):
    x=node('ShaderNodeVectorMath',operation=op); L.new(a,x.inputs[0])
    if op=='SCALE': x.inputs['Scale'].default_value=b
    elif isinstance(b,tuple): x.inputs[1].default_value=b
    else: L.new(b,x.inputs[1])
    return x.outputs[0]
def noise(v,scale,detail,rough=0.55,out='Fac'):
    x=node('ShaderNodeTexNoise'); x.inputs['Scale'].default_value=scale; x.inputs['Detail'].default_value=detail
    x.inputs['Roughness'].default_value=rough; L.new(v,x.inputs['Vector']); return x.outputs[out]
def ss(v,lo,hi):
    x=node('ShaderNodeMapRange',interpolation_type='SMOOTHSTEP'); x.inputs['From Min'].default_value=lo
    if isinstance(hi,(int,float)): x.inputs['From Max'].default_value=hi
    else: L.new(hi,x.inputs['From Max'])
    L.new(v,x.inputs['Value']); return x.outputs['Result']
def warp(v,scale,amt):
    return vm('ADD',v,vm('SCALE',vm('SUBTRACT',noise(v,scale,4,out='Color'),(0.5,0.5,0.5)),amt))
def line(n,level,w):   # 1 on the iso-contour n==level, width w (in noise units)
    return math('SUBTRACT',1.0,ss(math('ABSOLUTE',math('SUBTRACT',n,level)),0.0,w))

tc=node('ShaderNodeTexCoord'); tc.object=bpy.data.objects["MarbleSpace"]
P=tc.outputs['Object']
Pf=vm('MULTIPLY',P,(1.0,0.35,1.0))                     # flow direction
W=warp(warp(Pf,1.2,0.45),3.5,0.12)                      # strong two-level domain warp
sc=float(argv[1])
def family(W, sc, seed_shift):
    Ws=vm('ADD',W,seed_shift)
    n=noise(Ws,sc,7,rough=0.58)
    wmod=ss(noise(Ws,4.0,3),0.3,0.7)
    w=math('ADD',0.0015,math('MULTIPLY',wmod,0.008))
    main=line(n,0.5,w)
    sec=math('MULTIPLY',math('MAXIMUM',line(n,0.41,math('MULTIPLY',w,0.7)),line(n,0.59,math('MULTIPLY',w,0.7))),0.75)
    near=line(n,0.5,0.06)
    strands=math('MULTIPLY',math('MAXIMUM',line(n,0.462,math('MULTIPLY',w,0.4)),line(n,0.538,math('MULTIPLY',w,0.4))),near)
    return math('MAXIMUM',math('MAXIMUM',main,sec),math('MULTIPLY',strands,0.8)), near
fa,nearA=family(W,sc,(0,0,0))
Wb=warp(warp(vm('MULTIPLY',P,(0.35,1.0,1.0)),1.3,0.4),3.5,0.1)     # cross family, other direction
fb,nearB=family(Wb,sc*1.3,(7.3,1.1,3.9))
h=noise(warp(W,9.0,0.03),9.0,7,rough=0.58)
hair=math('MULTIPLY',line(h,0.5,0.007),math('MULTIPLY',math('MAXIMUM',nearA,nearB),0.6))
v=math('MAXIMUM',math('MAXIMUM',fa,math('MULTIPLY',fb,0.6)),hair)
inv=math('SUBTRACT',1.0,v)
em=node('ShaderNodeEmission'); L.new(inv,em.inputs[0]); o=node('ShaderNodeOutputMaterial'); L.new(em.outputs[0],o.inputs[0])
bpy.context.scene.view_settings.view_transform='Standard'
bpy.context.scene.render.filepath=argv[0]; bpy.ops.render.render(write_still=True)
