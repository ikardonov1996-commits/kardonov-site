import bpy
o=bpy.data.objects["Sculpture_HiRes"]
if o.animation_data and o.animation_data.action:
    for fc in o.animation_data.action.fcurves: print("FC",fc.data_path,fc.array_index,[(round(k.co[0]),round(k.co[1],3)) for k in fc.keyframe_points][:12])
for mn in ("Marble_Carve","Marble"):
    m=bpy.data.materials.get(mn)
    if not m: continue
    print("MAT",mn)
    for n in m.node_tree.nodes:
        extra=""
        if n.type=='ATTRIBUTE': extra=n.attribute_name
        if n.type=='TEX_COORD': extra=str(n.object)
        print("  ",n.type,n.name,extra,[ (i.name, tuple(i.default_value) if hasattr(i.default_value,'__len__') else i.default_value) for i in n.inputs if not i.is_linked and hasattr(i,'default_value')][:6])
me=o.data
print("attrs",[a.name for a in me.attributes],"uv",[u.name for u in me.uv_layers],"shape",me.shape_keys)
import numpy as np
co=np.empty(len(me.vertices)*3,np.float32); me.vertices.foreach_get("co",co); co=co.reshape(-1,3)
print("bbox",co.min(0),co.max(0))
