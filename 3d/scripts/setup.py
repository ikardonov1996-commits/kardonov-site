import bpy, sys, math
from mathutils import Vector
argv=sys.argv[sys.argv.index("--")+1:]
glb, out_blend, out_png = argv
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
sc=bpy.context.scene
mesh=[o for o in bpy.data.objects if o.type=='MESH'][0]
# drop the empty parent, keep world transform
mw=mesh.matrix_world.copy(); mesh.parent=None; mesh.matrix_world=mw
for o in list(bpy.data.objects):
    if o.type=='EMPTY': bpy.data.objects.remove(o)
mesh.name="Sculpture_HiRes"; mesh.data.name="Sculpture_HiRes"
bpy.context.view_layer.objects.active=mesh; mesh.select_set(True)
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
# origin at bottom center, standing on Z=0
bb=[mesh.matrix_world@Vector(c) for c in mesh.bound_box]
mn=Vector((min(v.x for v in bb),min(v.y for v in bb),min(v.z for v in bb)))
mx=Vector((max(v.x for v in bb),max(v.y for v in bb),max(v.z for v in bb)))
base=Vector(((mn.x+mx.x)/2,(mn.y+mx.y)/2,mn.z))
sc.cursor.location=base; bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
mesh.location=(0,0,0)
bpy.ops.object.shade_smooth()
h=mx.z-mn.z
print("DIMS",mesh.dimensions[:])
# collections
col=bpy.data.collections.new("Sculpture"); sc.collection.children.link(col)
for c in mesh.users_collection: c.objects.unlink(mesh)
col.objects.link(mesh)
# temp neutral material (marble comes next)
m=bpy.data.materials.new("Preview_Clay"); m.use_nodes=True
b=m.node_tree.nodes["Principled BSDF"]; b.inputs["Base Color"].default_value=(0.85,0.84,0.82,1); b.inputs["Roughness"].default_value=0.45
mesh.data.materials.append(m)
# camera + lights
cam=bpy.data.objects.new("Camera",bpy.data.cameras.new("Camera")); sc.collection.objects.link(cam)
cam.data.lens=50; sc.camera=cam
def look(o,target):
    d=Vector(target)-o.location; o.rotation_euler=d.to_track_quat('-Z','Y').to_euler()
cam.location=(h*0.9,-h*2.6,h*0.62); look(cam,(0,0,h*0.5))
for name,loc,energy,size in [("Key",(h*1.5,-h*1.5,h*2),800*h*h,h),("Fill",(-h*2,-h,h),200*h*h,h*2),("Rim",(0,h*2,h*1.8),500*h*h,h)]:
    L=bpy.data.objects.new(name,bpy.data.lights.new(name,'AREA')); L.data.energy=energy; L.data.size=size; L.location=loc; look(L,(0,0,h*0.5)); sc.collection.objects.link(L)
w=bpy.data.worlds.new("World"); w.use_nodes=True; w.node_tree.nodes["Background"].inputs[0].default_value=(0.02,0.02,0.022,1); sc.world=w
sc.render.engine='CYCLES'; sc.cycles.device='CPU'; sc.cycles.samples=64; sc.cycles.use_denoising=True
sc.render.resolution_x=900; sc.render.resolution_y=1200; sc.render.film_transparent=False
sc.view_settings.view_transform='AgX'
sc.frame_start=1; sc.frame_end=240; sc.render.fps=30
bpy.ops.wm.save_as_mainfile(filepath=out_blend, compress=True)
sc.render.filepath=out_png; bpy.ops.render.render(write_still=True)
