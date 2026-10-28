# Render each carving stage alone from the fixed 3/4 animation camera (fast EEVEE).
import bpy, sys
from mathutils import Vector
argv = sys.argv[sys.argv.index("--") + 1:]
sc = bpy.context.scene; O = bpy.data.objects
names = ["Marble_Block", "C1_Pitched", "C3_Relief2", "C4_Freed", "C5_Point", "C6_Claw", "Sculpture_HiRes"]
cam = sc.camera; cam.data.type = 'PERSP'; cam.data.lens = 85
cam.location = (1.35, -3.6, 0.95); d = Vector((0.03, 0, 0.57)) - cam.location; cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
sc.render.engine = 'BLENDER_EEVEE_NEXT'; sc.eevee.taa_render_samples = 8
sc.render.resolution_x = 600; sc.render.resolution_y = 800
for o in O:
    if o.name.startswith("Stage"): o.hide_render = True
    if o.name.startswith("MarbleSwatch"): o.hide_render = True
for i, keep in enumerate(names):
    for n in names: O[n].hide_render = (n != keep)
    sc.render.filepath = "%s/stage_%d.png" % (argv[0], i); bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)   # keep the camera setup in the anim file
