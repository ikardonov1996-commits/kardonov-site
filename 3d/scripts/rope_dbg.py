import bpy
for o in bpy.data.collections["Rope_Windlass"].all_objects:
    print(o.name, o.type, o.parent.name if o.parent else None, tuple(round(x,3) for x in o.matrix_world.translation), tuple(round(x,3) for x in o.dimensions))
