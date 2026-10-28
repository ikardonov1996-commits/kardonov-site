import bpy
for n in ("C2_Relief1", "C7_Rasp"):
    o = bpy.data.objects.get(n)
    if o: bpy.data.objects.remove(o)
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath, compress=True)
print("DROPPED", [o.name for o in bpy.data.objects if o.type == 'MESH'])
