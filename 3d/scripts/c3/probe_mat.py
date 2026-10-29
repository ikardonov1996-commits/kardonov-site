import bpy
for n in ("Neuro_Band_Glow","Neuro_Band","Neuro_Modules_Glow","Neuro_Modules"):
    o=bpy.data.objects[n]; print(n, [m.name for m in o.data.materials])
for m in bpy.data.materials:
    if m.name.startswith("Neuro"):
        nt=m.node_tree; print(m.name, [(nd.type, nd.name) for nd in nt.nodes])
        b=nt.nodes.get("Principled BSDF"); print("  ", tuple(b.inputs["Emission Color"].default_value), b.inputs["Emission Strength"].default_value, [l.from_node.name+"->"+l.to_node.name for l in nt.links])
