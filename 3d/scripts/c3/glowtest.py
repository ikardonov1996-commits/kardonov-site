import bpy, sys
import os
es, eg = float(os.environ["ES"]), float(os.environ["EG"])
def setm(n, base, emis, st):
    b=bpy.data.materials[n].node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value=(*base,1); b.inputs["Emission Color"].default_value=(*emis,1); b.inputs["Emission Strength"].default_value=st
setm("Neuro_GlowAmber",(0.05,0.015,0.0),(1.0,0.30,0.02),es)
setm("Neuro_GlowRing",(0.05,0.015,0.0),(1.0,0.30,0.02),es*1.2)
setm("Neuro_Lens",(0.30,0.10,0.02),(1.0,0.35,0.04),eg)
print(bpy.context.scene.view_settings.view_transform, bpy.context.scene.view_settings.look)
