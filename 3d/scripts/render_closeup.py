import bpy, sys
from mathutils import Vector
argv=sys.argv[sys.argv.index("--")+1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
sc=bpy.context.scene; cam=sc.camera
def look(o,t):
    d=Vector(t)-o.location; o.rotation_euler=d.to_track_quat('-Z','Y').to_euler()
bpy.data.objects["MarbleSwatch_Raw"].hide_render=True
cam.data.type='PERSP'; cam.data.lens=135; cam.location=(0.45,-1.6,0.85); look(cam,(0.0,0,0.70))
sc.render.filepath=argv[1]; bpy.ops.render.render(write_still=True)
