import bpy, sys
from mathutils import Vector
argv=sys.argv[sys.argv.index("--")+1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
sc=bpy.context.scene
ob=bpy.data.objects["Sculpture_HiRes"]
for o in bpy.data.objects:
    if o.name.startswith(("MarbleSwatch","Floor")): o.hide_render=True
g=bpy.data.materials.new('grey'); g.use_nodes=True; g.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(0.7,0.7,0.7,1)
ob.data.materials.clear(); ob.data.materials.append(g)
sc.cycles.samples=12; sc.render.resolution_x=1000; sc.render.resolution_y=800
cam=sc.camera; cam.data.type='ORTHO'
def look(o,t):
    d=Vector(t)-o.location; o.rotation_euler=d.to_track_quat('-Z','Y').to_euler()
shots={"front":((0,-2,0.69),(0,0,0.69),0.24),
       "side_r":((-2,-1.2,0.70),(-0.06,0,0.70),0.16),
       "side_l":((2,-1.4,0.70),(0.05,0,0.70),0.16),
       "navel":((0,-2,0.57),(0,0,0.57),0.10)}
for k,(loc,t,os_) in shots.items():
    cam.location=loc; look(cam,t); cam.data.ortho_scale=os_
    sc.render.filepath=argv[1]+"/chest_"+k+".png"; bpy.ops.render.render(write_still=True)
