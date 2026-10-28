import bpy, sys, time
argv = sys.argv[sys.argv.index("--") + 1:]
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = int(argv[2]); sc.cycles.use_denoising = True
sc.cycles.max_bounces = 4; sc.cycles.diffuse_bounces = 2; sc.cycles.glossy_bounces = 2; sc.cycles.transmission_bounces = 2
sc.cycles.transparent_max_bounces = 64; sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = 0.05
sc.cycles.denoiser = 'OPENIMAGEDENOISE'; sc.render.use_persistent_data = True
sc.render.resolution_x = int(argv[3]); sc.render.resolution_y = int(argv[3]) * 4 // 3
for f in [int(x) for x in argv[1].split(",")]:
    t = time.time(); sc.frame_set(f); sc.render.filepath = "%s/cy_%04d.png" % (argv[0], f); bpy.ops.render.render(write_still=True)
    print("CYTIME frame %d: %.1fs" % (f, time.time() - t))
