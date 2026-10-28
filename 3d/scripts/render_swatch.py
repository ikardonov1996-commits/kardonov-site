import bpy, sys
argv=sys.argv[sys.argv.index("--")+1:]
bpy.context.scene.render.filepath=argv[0]; bpy.ops.render.render(write_still=True)
