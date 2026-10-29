import bpy
sc=bpy.context.scene
w=sc.world; print("WORLD", w.name if w else None)
if w and w.use_nodes:
    for n in w.node_tree.nodes: print(" W", n.type, [(i.name, tuple(i.default_value) if hasattr(i.default_value,'__len__') else i.default_value) for i in n.inputs if not i.is_linked and hasattr(i,"default_value")][:3])
print("VIEW", sc.view_settings.view_transform, sc.view_settings.look, sc.view_settings.exposure)
for o in bpy.data.objects:
    if not o.name.startswith(("Robo_","Neuro_")): print("OBJ", o.name, o.type, o.hide_render, [m.name for m in getattr(o.data,'materials',[]) or []] if o.type=='MESH' else (o.data.type, o.data.energy) if o.type=='LIGHT' else '', tuple(round(x,2) for x in o.location))
for m in bpy.data.materials: print("MAT", m.name, m.users)
