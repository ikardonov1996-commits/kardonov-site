# Shared procedural marble. Texture lives in the space of empty "MarbleSpace",
# so the raw block and the sculpture reveal the same veins when carved.
# Per-object property "polish" (0 = raw quarried stone, 1 = polished) drives finish.
import bpy, sys
from mathutils import Vector
argv=sys.argv[sys.argv.index("--")+1:]
blend, out_dir = argv
bpy.ops.wm.open_mainfile(filepath=blend)
sc=bpy.context.scene
sculpt=bpy.data.objects["Sculpture_HiRes"]

space=bpy.data.objects.get("MarbleSpace") or bpy.data.objects.new("MarbleSpace",None)
if space.name not in sc.collection.objects: sc.collection.objects.link(space)
space.empty_display_type='CUBE'; space.empty_display_size=0.5
space.location=(0,0,0.5); space.rotation_euler=(0.35,0.6,0.25)

m=bpy.data.materials.get("Marble") or bpy.data.materials.new("Marble")
m.use_nodes=True; nt=m.node_tree; N=nt.nodes; L=nt.links; N.clear()
def n(t,x,y,**kw):
    node=N.new(t); node.location=(x*220,y*220)
    for k,v in kw.items(): setattr(node,k,v)
    return node
def math(op,a,b=None,x=0,y=0):
    node=n('ShaderNodeMath',x,y,operation=op)
    for i,v in enumerate((a,b)):
        if v is None: continue
        if isinstance(v,(int,float)): node.inputs[i].default_value=v
        else: L.new(v,node.inputs[i])
    return node.outputs[0]
def ramp(src,stops,x,y,label=''):
    r=n('ShaderNodeValToRGB',x,y); r.label=label; e=r.color_ramp.elements
    while len(e)<len(stops): e.new(0)
    for el,(p,c) in zip(e,stops): el.position=p; el.color=c if len(c)==4 else (*c,1)
    L.new(src,r.inputs['Fac']); return r
out=n('ShaderNodeOutputMaterial',12,0)
bsdf=n('ShaderNodeBsdfPrincipled',10,0); L.new(bsdf.outputs[0],out.inputs['Surface'])
tc=n('ShaderNodeTexCoord',-8,0); tc.object=space
polish=n('ShaderNodeAttribute',-8,-6,attribute_type='OBJECT',attribute_name='polish').outputs['Fac']
gold=n('ShaderNodeAttribute',-8,-7,attribute_type='OBJECT',attribute_name='gold').outputs['Fac']
P=tc.outputs['Object']

# domain warp: P + (noise-0.5)*amount  (keeps real-world scale)
def warp(vec,scale,amount,x,y):
    t=n('ShaderNodeTexNoise',x,y); t.inputs['Scale'].default_value=scale; t.inputs['Detail'].default_value=5
    L.new(vec,t.inputs['Vector'])
    sub=n('ShaderNodeVectorMath',x+1,y,operation='SUBTRACT'); L.new(t.outputs['Color'],sub.inputs[0]); sub.inputs[1].default_value=(0.5,0.5,0.5)
    sc_=n('ShaderNodeVectorMath',x+1.5,y,operation='SCALE'); L.new(sub.outputs[0],sc_.inputs[0]); sc_.inputs['Scale'].default_value=amount
    add=n('ShaderNodeVectorMath',x+2,y,operation='ADD'); L.new(vec,add.inputs[0]); L.new(sc_.outputs[0],add.inputs[1])
    return add.outputs[0]
W1=warp(P,2.0,0.18,-7,3)
W2=warp(W1,7.0,0.05,-7,5)
W=warp(W2,30.0,0.008,-7,7)

# crack network = distance to Voronoi edge; width modulated so veins fade in and out
def cracks(scale,wmin,wmax,x,y):
    v=n('ShaderNodeTexVoronoi',x,y,feature='DISTANCE_TO_EDGE'); v.inputs['Scale'].default_value=scale; v.inputs['Randomness'].default_value=1.0
    L.new(W,v.inputs['Vector'])
    wn=n('ShaderNodeTexNoise',x,y-1); wn.inputs['Scale'].default_value=scale*0.6; wn.inputs['Detail'].default_value=3
    L.new(W,wn.inputs['Vector'])
    wr=n('ShaderNodeMapRange',x+1,y-1); wr.inputs['From Min'].default_value=0.38; wr.inputs['From Max'].default_value=0.68
    wr.inputs['To Min'].default_value=wmin; wr.inputs['To Max'].default_value=wmax; L.new(wn.outputs['Fac'],wr.inputs['Value'])
    q=math('DIVIDE',v.outputs['Distance'],wr.outputs['Result'],x+2,y)      # 0 at crack centre, 1 at edge of vein
    core=math('SUBTRACT',1.0,math('MINIMUM',q,1.0,x+2.5,y),x+3,y)          # 1..0
    halo=math('SUBTRACT',1.0,math('MINIMUM',math('MULTIPLY',q,0.15,x+2.5,y-0.5),1.0,x+2.7,y-0.5),x+3,y-0.5)
    return math('POWER',core,1.6,x+3.5,y), math('POWER',halo,2.5,x+3.5,y-0.5)
c1,h1=cracks(5.5,0.0005,0.016,-3,4)
c2,h2=cracks(16.0,0.0002,0.006,-3,1)
c3,h3=cracks(38.0,0.0001,0.0025,-3,-1)
core=math('MAXIMUM',math('MAXIMUM',c1,math('MULTIPLY',c2,0.85,1,1),1.2,3),math('MULTIPLY',c3,0.45,1,0),1.5,3)
halo=math('MAXIMUM',h1,math('MULTIPLY',h2,0.5,1,0.5),1.5,2)

# body: warm ivory with soft clouds
cl=n('ShaderNodeTexNoise',-3,-2); cl.inputs['Scale'].default_value=3.0; cl.inputs['Detail'].default_value=8; cl.inputs['Roughness'].default_value=0.6
L.new(W1,cl.inputs['Vector'])
body=ramp(cl.outputs['Fac'],[(0.3,(0.84,0.70,0.60)),(0.55,(0.92,0.83,0.76)),(0.78,(0.96,0.91,0.86))],-1,-2,'Body')
mh=n('ShaderNodeMix',3,0,data_type='RGBA'); L.new(math('MULTIPLY',halo,0.75,2.5,1),mh.inputs['Factor'])
L.new(body.outputs['Color'],mh.inputs['A']); mh.inputs['B'].default_value=(0.88,0.60,0.38,1)
veincol=ramp(core,[(0.0,(0.80,0.50,0.25)),(0.8,(0.62,0.33,0.13)),(1.0,(0.45,0.22,0.08))],2.5,-1,'Vein colour')
mc=n('ShaderNodeMix',4,0,data_type='RGBA'); L.new(core,mc.inputs['Factor'])
L.new(mh.outputs['Result'],mc.inputs['A']); L.new(veincol.outputs['Color'],mc.inputs['B'])
# gold option (object prop "gold"=1): veins become metallic gold
gcol=n('ShaderNodeMix',5,0,data_type='RGBA'); L.new(math('MULTIPLY',core,gold,4.5,-1),gcol.inputs['Factor'])
L.new(mc.outputs['Result'],gcol.inputs['A']); gcol.inputs['B'].default_value=(1.0,0.70,0.30,1)
# raw stone: dusty and paler
dust=n('ShaderNodeMix',6,0,data_type='RGBA'); dust.inputs['B'].default_value=(0.90,0.86,0.82,1)
L.new(math('MULTIPLY',math('SUBTRACT',1.0,polish,5,-3),0.3,5.5,-3),dust.inputs['Factor'])
L.new(gcol.outputs['Result'],dust.inputs['A']); xt=n('ShaderNodeTexVoronoi',6,2); xt.inputs['Scale'].default_value=900; L.new(P,xt.inputs['Vector'])
xr=n('ShaderNodeMapRange',7,2); xr.inputs['To Min'].default_value=0.94; xr.inputs['To Max'].default_value=1.04; L.new(xt.outputs['Distance'],xr.inputs['Value'])
xm=n('ShaderNodeMix',7.5,0,data_type='RGBA',blend_type='MULTIPLY'); xm.inputs['Factor'].default_value=1.0
L.new(dust.outputs['Result'],xm.inputs['A']); L.new(xr.outputs['Result'],xm.inputs['B'])
L.new(xm.outputs['Result'],bsdf.inputs['Base Color'])
L.new(math('MULTIPLY',core,gold,8,-1),bsdf.inputs['Metallic'])

rough=n('ShaderNodeMapRange',8,-3); rough.inputs['To Min'].default_value=0.75; rough.inputs['To Max'].default_value=0.46
L.new(polish,rough.inputs['Value'])
rv=n('ShaderNodeTexNoise',8,-4.5); rv.inputs['Scale'].default_value=25; L.new(P,rv.inputs['Vector'])
rr=math('ADD',rough.outputs['Result'],math('MULTIPLY',math('SUBTRACT',rv.outputs['Fac'],0.5,8.5,-4.5),0.25,8.8,-4.5),9,-3.5)
L.new(math('ADD',rr,math('MULTIPLY',core,0.12,9,-4.8),9.3,-3.5),bsdf.inputs['Roughness'])
bsdf.inputs['Subsurface Weight'].default_value=0.6
bsdf.inputs['Subsurface Radius'].default_value=(1.0,0.72,0.5)
bsdf.inputs['Subsurface Scale'].default_value=0.006
bsdf.inputs['Coat Roughness'].default_value=0.25
bsdf.inputs['Coat Weight'].default_value=0.0
bsdf.inputs['Specular IOR Level'].default_value=0.4

# chisel grain + veins slightly recessed; strong when raw
grain=n('ShaderNodeTexNoise',6,-6); grain.inputs['Scale'].default_value=160; grain.inputs['Detail'].default_value=4; L.new(P,grain.inputs['Vector'])
chips=n('ShaderNodeTexVoronoi',6,-8); chips.inputs['Scale'].default_value=45; L.new(P,chips.inputs['Vector'])
height=math('SUBTRACT',math('ADD',grain.outputs['Fac'],chips.outputs['Distance'],7,-7),math('MULTIPLY',core,0.3,7,-8),7.5,-7)
bstr=n('ShaderNodeMapRange',7,-9); bstr.inputs['To Min'].default_value=0.4; bstr.inputs['To Max'].default_value=0.03; L.new(polish,bstr.inputs['Value'])
bump=n('ShaderNodeBump',9,-7); bump.inputs['Distance'].default_value=0.002
L.new(bstr.outputs['Result'],bump.inputs['Strength']); L.new(height,bump.inputs['Height']); L.new(bump.outputs['Normal'],bsdf.inputs['Normal'])

sculpt.data.materials.clear(); sculpt.data.materials.append(m)
sculpt["polish"]=1.0; sculpt["gold"]=0.0
old=bpy.data.materials.get("Preview_Clay")
if old: bpy.data.materials.remove(old)

# test swatch: raw stone cube from the same marble
if "MarbleSwatch_Raw" not in bpy.data.objects:
    bpy.ops.mesh.primitive_cube_add(size=0.3,location=(0.45,0.15,0.15))
    sw=bpy.context.active_object; sw.name="MarbleSwatch_Raw"
    bpy.ops.object.modifier_add(type='BEVEL'); sw.modifiers[-1].width=0.01; sw.modifiers[-1].segments=3
sw=bpy.data.objects["MarbleSwatch_Raw"]; sw.location=(-0.36,0.45,0.11); sw.scale=(0.75,0.75,0.75); sw.data.materials.clear(); sw.data.materials.append(m); sw["polish"]=0.0; sw["gold"]=0.0

# camera/light/floor tuning
def look(o,t):
    d=Vector(t)-o.location; o.rotation_euler=d.to_track_quat('-Z','Y').to_euler()
cam=sc.camera; cam.data.lens=85; cam.location=(1.0,-2.75,0.75); look(cam,(0.08,0,0.5))
for nm,loc,e,s in [("Key",(1.4,-1.3,2.0),150,0.8),("Fill",(-2.0,-1.2,0.9),35,2.0),("Rim",(-0.6,1.8,1.7),260,0.6)]:
    l=bpy.data.objects[nm]; l.data.color={'Key':(1,0.86,0.72),'Fill':(0.85,0.88,1),'Rim':(1,0.8,0.6)}[nm]; l.location=loc; l.data.energy=e; l.data.size=s; look(l,(0,0,0.5))
if "Floor" not in bpy.data.objects:
    bpy.ops.mesh.primitive_plane_add(size=12); f=bpy.context.active_object; f.name="Floor"
    fm=bpy.data.materials.new("Floor_Dark"); fm.use_nodes=True
    p=fm.node_tree.nodes["Principled BSDF"]; p.inputs["Base Color"].default_value=(0.025,0.025,0.027,1); p.inputs["Roughness"].default_value=0.6
    f.data.materials.append(fm)
sc.cycles.samples=48
bpy.ops.wm.save_as_mainfile(filepath=blend,compress=True)

sc.render.filepath=out_dir+"/marble_full.png"; bpy.ops.render.render(write_still=True)
# close-up of head/torso
cam.data.lens=135; cam.location=(0.55,-1.55,0.95); look(cam,(0.02,0,0.78))
sw.hide_render=True
sc.render.filepath=out_dir+"/marble_closeup.png"; bpy.ops.render.render(write_still=True)
