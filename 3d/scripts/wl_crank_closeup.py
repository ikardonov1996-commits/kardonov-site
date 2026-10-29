# crank close-up from the site direction. args: -- out.png
import bpy, sys, math
from mathutils import Vector
out = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene; O = bpy.data.objects
sc.render.engine = 'BLENDER_EEVEE_NEXT'; sc.eevee.taa_render_samples = 32
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 900, 900, 100
sc.render.film_transparent = True; sc.render.use_border = False
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'
dg = bpy.context.evaluated_depsgraph_get()
pts = []
for n in ("Crank", "Crank_Boss", "Crank_Grip"):
    e = O[n].evaluated_get(dg); pts += [e.matrix_world @ Vector(c) for c in e.bound_box]
ctr = sum(pts, Vector()) / len(pts)
d = Vector((1.35, -3.6, 0.0)).normalized()
cam = sc.camera; cam.data.type = 'ORTHO'; cam.data.ortho_scale = 0.62
cam.location = ctr + d * 6.0; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
cam.data.clip_start, cam.data.clip_end = 0.01, 100
sc.render.filepath = out; bpy.ops.render.render(write_still=True); print("RENDERED", out)
