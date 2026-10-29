import bpy, numpy as np
from mathutils import Vector as V
HC=V((-0.031,-0.002,0))
for n in ("Neuro_Band","Neuro_Band_Glow","Neuro_Band_LipTop"):
    o=bpy.data.objects[n]; me=o.data
    co=np.array([tuple(o.matrix_world@v.co) for v in me.vertices])
    r=np.hypot(co[:,0]-HC.x, co[:,1]-HC.y); print(n, len(co), "r", r.min(), r.max(), "z", co[:,2].min(), co[:,2].max(), "hide", o.hide_render, o.hide_get(), [m.type for m in o.modifiers])
