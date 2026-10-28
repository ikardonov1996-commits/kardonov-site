import bpy, sys
argv = sys.argv[sys.argv.index("--") + 1:]
sc = bpy.context.scene; O = bpy.data.objects
sc.render.engine = 'BLENDER_EEVEE_NEXT'; sc.eevee.taa_render_samples = 8
sc.render.resolution_x = 300; sc.render.resolution_y = 400
sc.frame_set(132)
for solo in ("C3_Relief2", "C4_Freed"):
    for n in ("Marble_Block", "C1_Pitched", "C3_Relief2", "C4_Freed", "C5_Point", "C6_Claw", "Sculpture_HiRes"):
        O[n].hide_render = (n != solo)
    sc.render.filepath = "%s/solo_%s.png" % (argv[0], solo); bpy.ops.render.render(write_still=True)
m = bpy.data.materials["Marble_Carve"]
print("MAT", m.surface_render_method, getattr(m, "use_transparent_shadow", "n/a"), m.blend_method, m.shadow_method if hasattr(m, "shadow_method") else "")
