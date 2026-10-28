import bpy
for o in bpy.data.objects:
    print("OBJ", o.name, o.type, o.parent.name if o.parent else None, tuple(round(x,3) for x in o.location), tuple(round(x,3) for x in o.rotation_euler), tuple(round(x,3) for x in o.scale), tuple(round(x,3) for x in o.dimensions), dict(o.items()) if o.keys() else "")
    if o.type=='CAMERA': print("  cam", o.data.lens, o.data.type, o.matrix_world.translation)
    if o.type=='LIGHT': print("  light", o.data.type, o.data.energy)
sc=bpy.context.scene
print(sc.render.engine, sc.render.resolution_x, sc.render.resolution_y, sc.frame_start, sc.frame_end, sc.render.fps, sc.world.name if sc.world else None)
print("mats", [m.name for m in bpy.data.materials])
m=bpy.data.materials['Marble']
for n in m.node_tree.nodes:
    if n.type in('TEX_COORD','ATTRIBUTE'): print(n.name, n.type, getattr(n,'object',None), getattr(n,'attribute_name',None))
b=bpy.data.objects['Marble_Block']
import mathutils
bb=[b.matrix_world@mathutils.Vector(c) for c in b.bound_box]
print("bbmin", [min(v[i] for v in bb) for i in range(3)], "bbmax",[max(v[i] for v in bb) for i in range(3)])
print("mods", [(md.name, md.type) for md in b.modifiers])
