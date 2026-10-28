# Final stage stills for the site: Cycles, transparent background, floor as shadow catcher.
import bpy, sys
argv = sys.argv[sys.argv.index("--") + 1:]
out = argv[0]
sc = bpy.context.scene; O = bpy.data.objects
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 48; sc.cycles.use_denoising = True
sc.cycles.denoiser = 'OPENIMAGEDENOISE'; sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = 0.02
sc.cycles.max_bounces = 6; sc.cycles.transparent_max_bounces = 64
sc.render.resolution_x = 1080; sc.render.resolution_y = 1440; sc.render.resolution_percentage = 100
sc.render.film_transparent = True
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'
O["Floor"].is_shadow_catcher = True
names = ["Marble_Block", "C1_Pitched", "C3_Relief2", "C4_Freed", "C5_Point", "C6_Claw", "Sculpture_HiRes"]
frames = list(sc["stage_frames"])
only = [int(x) for x in argv[1].split(",")] if len(argv) > 1 else range(len(names))
for i in only:
    import os
    if os.path.exists("%s/stage_%d_%s.png" % (out, i + 1, names[i])): print("STILL", i + 1, names[i], "(exists)", flush=True); continue
    sc.frame_set(frames[i])
    for n in names: O[n].hide_render = (n != names[i])     # exactly one stage per still
    sc.render.filepath = "%s/stage_%d_%s.png" % (out, i + 1, names[i]); bpy.ops.render.render(write_still=True)
    print("STILL", i + 1, names[i], flush=True)
