import bpy
for m in bpy.data.materials:
    if m.name.startswith("Marble"):
        print("MAT", m.name)
        for n in m.node_tree.nodes:
            extra = ""
            if n.type=='TEX_COORD': extra = str(n.object)
            if n.type=='ATTRIBUTE': extra = n.attribute_name + " " + n.attribute_type
            ins = [(i.name, tuple(i.default_value) if hasattr(i.default_value,'__len__') else i.default_value) for i in n.inputs if not i.is_linked and hasattr(i,'default_value')][:6]
            print("  ", n.type, n.name, extra, ins)
o = bpy.data.objects.get("MarbleSpace")
print("MS", o and (o.type, tuple(o.location), tuple(o.scale), tuple(o.rotation_euler)))
for o in bpy.data.objects:
    if o.type in ('LIGHT','CAMERA','EMPTY') or len(o.keys()): print("OBJ", o.name, o.type, tuple(round(x,2) for x in o.location), o.type=='LIGHT' and (o.data.type, o.data.energy, tuple(o.data.color), getattr(o.data,'size',0)), dict((k,o[k]) for k in o.keys() if isinstance(o[k],(int,float))))
w = bpy.context.scene.world
if w and w.use_nodes:
    for n in w.node_tree.nodes: print("WORLD", n.type, [(i.name, getattr(i,'default_value',None) if not hasattr(getattr(i,'default_value',None),'__len__') else tuple(i.default_value)) for i in n.inputs])
sc=bpy.context.scene; print("VT", sc.view_settings.view_transform, sc.view_settings.look, sc.view_settings.exposure)
