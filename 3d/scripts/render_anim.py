# Full animation render, Cycles (clean with the overlapping stage shells). Resumable: skips frames on disk.
import bpy, sys
argv = sys.argv[sys.argv.index("--") + 1:]
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 16; sc.cycles.use_denoising = True
sc.cycles.denoiser = 'OPENIMAGEDENOISE'; sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = 0.05
sc.cycles.max_bounces = 4; sc.cycles.diffuse_bounces = 2; sc.cycles.glossy_bounces = 2; sc.cycles.transmission_bounces = 2
sc.cycles.transparent_max_bounces = 64
sc.render.resolution_x = 540; sc.render.resolution_y = 720; sc.render.resolution_percentage = 100
sc.render.use_persistent_data = True
sc.render.image_settings.file_format = 'PNG'
sc.render.filepath = argv[0] + "/frame_"
sc.render.use_overwrite = False; sc.render.use_placeholder = True
bpy.ops.render.render(animation=True)
