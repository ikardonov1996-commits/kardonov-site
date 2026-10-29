import bpy
O=bpy.data.objects
def desc(r):
    return [o for o in O if any(p==r for p in [o.parent, o.parent and o.parent.parent, o.parent and o.parent.parent and o.parent.parent.parent])]
for o in sorted(desc(O["Windlass"]), key=lambda o:o.name):
    print(o.name, o.type, o.parent.name, [s.material.name if s.material else None for s in o.material_slots], tuple(round(x,3) for x in o.dimensions))
for m in bpy.data.materials:
    if m.use_nodes:
        b=[n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED']
        if b: print("MAT",m.name, tuple(round(x,3) for x in b[0].inputs['Base Color'].default_value[:3]), b[0].inputs['Base Color'].is_linked, round(b[0].inputs['Metallic'].default_value,2), round(b[0].inputs['Roughness'].default_value,2))
