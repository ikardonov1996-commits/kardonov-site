import bpy, sys
argv = sys.argv[sys.argv.index("--") + 1:]
sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE_NEXT'; sc.eevee.taa_render_samples = 8
sc.render.resolution_x = 300; sc.render.resolution_y = 400
sc.frame_set(132)
m = bpy.data.materials["Marble_Carve"]
b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
b.inputs['Subsurface Weight'].default_value = 0.0
sc.render.filepath = argv[0] + "/nosss.png"; bpy.ops.render.render(write_still=True)
b.inputs['Subsurface Weight'].default_value = 0.6
sc.eevee.use_shadows = False
sc.render.filepath = argv[0] + "/noshadow.png"; bpy.ops.render.render(write_still=True)
