import bpy
for mn in ("Marble","Rope_Hemp","Wood_Aged","AI_Titanium"):
    m=bpy.data.materials[mn]
    for n in m.node_tree.nodes:
        extra=""
        if n.type=='BSDF_PRINCIPLED':
            extra=" ".join(f"{k}={n.inputs[k].default_value if not hasattr(n.inputs[k].default_value,'__len__') else tuple(round(x,3) for x in n.inputs[k].default_value)}{'(L)' if n.inputs[k].is_linked else ''}" for k in ("Subsurface Weight","Subsurface Scale","Subsurface Radius","Coat Weight","Transmission Weight","Roughness","Specular IOR Level"))
            extra+=" sssmethod="+n.subsurface_method
        print("N",mn,n.type,n.name,extra)
    print("DISP",mn,m.cycles.displacement_method if hasattr(m.cycles,'displacement_method') else m.displacement_method)
o=bpy.data.objects["Marble_Block"]; print("MB polys",len(o.data.polygons),[md.type for md in o.modifiers])
