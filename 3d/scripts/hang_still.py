# Still of the block hanging on its rope (rope cropped at the top edge), for a CSS-swung photo on the site.
# Swing removed (block hangs plumb), windlass hidden, transparent background, orthographic 3/4 view.
import bpy, sys, numpy as np
from mathutils import Vector
argv = sys.argv[sys.argv.index("--") + 1:]
out, samples = argv[0], int(argv[1])
sc = bpy.context.scene; O = bpy.data.objects
sc.frame_set(120)
for n in ("Hang_Pivot", "Hang_Drop"):                     # kill the baked swing/twist, keep the descent
    o = O[n]
    if o.animation_data and o.animation_data.action:
        for fc in list(o.animation_data.action.fcurves):
            if fc.data_path == "rotation_euler": o.animation_data.action.fcurves.remove(fc)
    o.rotation_euler = (0, 0, 0)
sc.frame_set(120)
hide = {o.name for o in O if o.name == "Windlass" or (o.parent and o.parent.name in ("Windlass", "Drum")) or o.name in ("Drum", "Rope_DrumCoil")}
hide |= {o.name for o in O if o.parent and o.parent.name == "Drum"}
for n in hide: O[n].hide_render = True
dg = bpy.context.evaluated_depsgraph_get()
blk = O["Marble_Block"].evaluated_get(dg)
bb = np.array([blk.matrix_world @ Vector(c) for c in blk.bound_box])
top_rope = O["Hang_Pivot"].matrix_world.translation
cx, cy = bb[:, 0].mean(), bb[:, 1].mean()
zmin = bb[:, 2].min(); zmax = bb[:, 2].max()
# camera: horizontal 3/4 view, ortho, block in lower part, rope runs up out of frame
d = Vector((1.35, -3.6, 0.0)).normalized()
H = (zmax - zmin) * 2.15                                   # frame height: block + ~1.1 block-heights of rope
cam = sc.camera; cam.data.type = 'ORTHO'; cam.data.ortho_scale = H   # height is the long side (portrait)
zc = zmin - 0.06 + H / 2
cam.location = Vector((cx, cy, zc)) + d * 10.0
cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
sc.render.resolution_x = 1080; sc.render.resolution_y = 1920
sc.render.film_transparent = True
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'
sc.render.engine = 'CYCLES'; sc.cycles.samples = samples; sc.cycles.use_denoising = True; sc.cycles.transparent_max_bounces = 64
# where the rope leaves the top edge (pixels) = CSS transform-origin for the swing
from bpy_extras.object_utils import world_to_camera_view
p = world_to_camera_view(sc, cam, Vector((top_rope.x, top_rope.y, zc + H / 2)))
print("ROPE_TOP_PX x=%.0f y=0  (of 1080x1920)" % (p.x * 1080))
sc.render.filepath = out; bpy.ops.render.render(write_still=True)
print("HANG DONE")
