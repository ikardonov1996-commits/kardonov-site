import bpy, sys
argv = sys.argv[sys.argv.index("--") + 1:]
sc = bpy.context.scene; O = bpy.data.objects
sc.render.engine = 'CYCLES'; sc.cycles.samples = 8; sc.cycles.use_denoising = True
sc.render.resolution_x = 300; sc.render.resolution_y = 400
sc.frame_set(279)
ALL = ("Marble_Block", "C1_Pitched", "C3_Relief2", "C4_Freed", "C5_Point", "C6_Claw", "Sculpture_HiRes")
for solo in ("C6_Claw", "Sculpture_HiRes"):
    for n in ALL: O[n].hide_render = (n != solo)
    print("PROPS", solo, O[solo]["f_in"], O[solo]["f_out"])
    sc.render.filepath = "%s/cysolo_%s.png" % (argv[0], solo); bpy.ops.render.render(write_still=True)
