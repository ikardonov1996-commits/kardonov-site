import bpy
m=bpy.data.materials["AI_Titanium"]; b=m.node_tree.nodes["Principled BSDF"]
print("TI", tuple(round(x,3) for x in b.inputs["Base Color"].default_value), b.inputs["Metallic"].default_value, b.inputs["Anisotropic"].default_value)
for o in bpy.data.objects:
    ms=[s.material.name for s in o.material_slots if s.material]
    if any("Glow" in x for x in ms): print("GLOW", o.name, ms, getattr(o.data,'bevel_depth',None))
print("MATS", sorted(m.name for m in bpy.data.materials))
