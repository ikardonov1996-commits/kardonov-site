import bpy
m=bpy.data.materials["Tool_Gunmetal"]
for n in m.node_tree.nodes:
    print(n.type, n.name, [(i.name, tuple(i.default_value) if hasattr(i.default_value,'__len__') else i.default_value) for i in n.inputs if i.is_linked is False and i.name in ("Base Color","Metallic","Roughness","Scale","Color")][:5])
