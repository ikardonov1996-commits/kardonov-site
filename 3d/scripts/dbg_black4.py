import bpy, sys
argv = sys.argv[sys.argv.index("--") + 1:]
sc = bpy.context.scene; e = sc.eevee
print("EEVEE props:", [p for p in dir(e) if any(k in p for k in ("gi", "ray", "horizon", "fast", "ao", "thick", "shadow"))])
sc.render.engine = 'BLENDER_EEVEE_NEXT'; e.taa_render_samples = 8
sc.render.resolution_x = 300; sc.render.resolution_y = 400
sc.frame_set(132)
for p, v in (("fast_gi_method", None), ("use_fast_gi", False), ("use_raytracing", False), ("horizon_bias", 0.0)):
    pass
if hasattr(e, "fast_gi_distance"): e.fast_gi_distance = 0.0
if hasattr(e, "fast_gi_resolution"): pass
if hasattr(e, "use_gtao"): e.use_gtao = False
if hasattr(e, "gtao_distance"): e.gtao_distance = 0.0
sc.render.filepath = argv[0] + "/nogi.png"; bpy.ops.render.render(write_still=True)
