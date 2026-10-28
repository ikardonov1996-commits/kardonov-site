import bpy, sys, numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree
argv=sys.argv[sys.argv.index("--")+1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
sc=bpy.context.scene
ob=bpy.data.objects["Sculpture_HiRes"]; me=ob.data
n=len(me.vertices)
co=np.empty(n*3,np.float32); me.vertices.foreach_get('co',co); co=co.reshape(-1,3)
no=np.empty(n*3,np.float32); me.vertices.foreach_get('normal',no); no=no.reshape(-1,3)
sel=np.where((co[:,2]>0.45)&(co[:,2]<0.80)&(np.abs(co[:,0])<0.12)&(no[:,1]<-0.3))[0]
kd=KDTree(n)
for i,c in enumerate(co): kd.insert(c,i)
kd.balance()
cand=sel[::3]; prot=np.zeros(len(cand))
for k,i in enumerate(cand):
    idx=[j for _,j,_ in kd.find_range(co[i],0.012)]
    prot[k]=np.dot(co[i]-co[idx].mean(0),no[i])
picked=[]
for k in np.argsort(-np.abs(prot)):
    p=co[cand[k]]
    if any(np.linalg.norm(p-q)<0.025 for q,_ in picked): continue
    picked.append((p,prot[k]))
    if len(picked)>=10: break
for o in list(bpy.data.objects):
    if o.name.startswith(("MarbleSwatch","Floor")): o.hide_render=True
ob.data.materials.clear(); g=bpy.data.materials.new('grey'); g.use_nodes=True; g.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(0.7,0.7,0.7,1); ob.data.materials.append(g)
for k,(p,v) in enumerate(picked):
    print("MARK %d %.4f %.4f %.4f prot=%.5f"%(k,p[0],p[1],p[2],v))
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.004,location=p)
    s=bpy.context.active_object; s.name="mark%d"%k
    m=bpy.data.materials.new("m%d"%k); m.use_nodes=True; nt=m.node_tree; nt.nodes.clear()
    e=nt.nodes.new('ShaderNodeEmission'); e.inputs[0].default_value=(1,0,0,1) if v>0 else (0,0.3,1,1); e.inputs[1].default_value=3
    o=nt.nodes.new('ShaderNodeOutputMaterial'); nt.links.new(e.outputs[0],o.inputs[0]); s.data.materials.append(m)
    bpy.ops.object.text_add(location=(p[0]+0.006,p[1]-0.02,p[2]+0.004)); t=bpy.context.active_object
    t.data.body=str(k); t.data.size=0.014; t.rotation_euler=(1.5708,0,0); t.data.materials.append(m)
cam=sc.camera; cam.data.type='ORTHO'; cam.data.ortho_scale=0.42; cam.location=(0,-2,0.62); cam.rotation_euler=(1.5708,0,0)
sc.cycles.samples=12
sc.render.resolution_x=900; sc.render.resolution_y=1100
sc.render.filepath=argv[1]; bpy.ops.render.render(write_still=True)
