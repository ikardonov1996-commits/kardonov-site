import bpy, sys
argv = sys.argv[sys.argv.index("--") + 1:]
sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE_NEXT'; sc.eevee.taa_render_samples = 8
sc.render.resolution_x = 300; sc.render.resolution_y = 400
sc.frame_set(132)
m = bpy.data.materials["Marble_Carve"]
m.surface_render_method = 'BLENDED'; m.use_backface_culling = False
sc.render.filepath = argv[0] + "/blended.png"; bpy.ops.render.render(write_still=True)
m.surface_render_method = 'DITHERED'
sc.eevee.use_raytracing = False; sc.eevee.fast_gi_method = 'GLOBAL_ILLUMINATION' if hasattr(sc.eevee, 'fast_gi_method') else None
for attr in ("use_gtao",):
    if hasattr(sc.eevee, attr): setattr(sc.eevee, attr, False)
sc.eevee.horizon_quality = 0.0 if hasattr(sc.eevee, "horizon_quality") else None
sc.render.filepath = argv[0] + "/nogi.png"; bpy.ops.render.render(write_still=True)
