import bpy
m=bpy.data.materials['Floor_Dark']
for n in m.node_tree.nodes:
    print(n.type, n.name)
    if n.type=='BSDF_PRINCIPLED':
        for k in ("Base Color","Roughness","Metallic","Specular IOR Level","Coat Weight"): print("  ",k, tuple(n.inputs[k].default_value) if hasattr(n.inputs[k].default_value,'__len__') else n.inputs[k].default_value, n.inputs[k].is_linked)
print(bpy.data.objects['Floor'].dimensions)
