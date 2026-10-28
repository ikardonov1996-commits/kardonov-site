import bpy,sys
argv=sys.argv[sys.argv.index("--")+1:]
for n in argv[3].split(","):
    if n in bpy.data.objects: bpy.data.objects[n].hide_render=True
