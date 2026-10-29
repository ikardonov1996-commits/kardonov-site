# Final still of the rebuilt C4_Freed with exactly the render_stills.py settings (resumable: skips if present).
# usage: blender -b anim_carving.blend -P render_c4.py -- OUT.png
import bpy, sys, os
out = sys.argv[sys.argv.index("--") + 1:][0]
if os.path.exists(out): print("STILL exists", out); sys.exit(0)
sc = bpy.context.scene; O = bpy.data.objects
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 48; sc.cycles.use_denoising = True
sc.cycles.denoiser = 'OPENIMAGEDENOISE'; sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = 0.02
sc.cycles.max_bounces = 6; sc.cycles.transparent_max_bounces = 64
sc.render.resolution_x = 1080; sc.render.resolution_y = 1440; sc.render.resolution_percentage = 100
sc.render.film_transparent = True
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'
O["Floor"].is_shadow_catcher = True
names = ["Marble_Block", "C1_Pitched", "C3_Relief2", "C4_Freed", "C5_Point", "C6_Claw", "Sculpture_HiRes"]
assert O["C4_Freed"].get("c4_version") == 2, "C4_Freed not rebuilt"
sc.frame_set(list(sc["stage_frames"])[3])
for n in names: O[n].hide_render = (n != "C4_Freed")
tmp = out + ".part.png"
sc.render.filepath = tmp; bpy.ops.render.render(write_still=True)
os.replace(tmp, out); print("STILL", out, flush=True)
