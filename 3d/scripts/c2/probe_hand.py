import bpy, numpy as np
a=bpy.data.objects["ArmRef"]; me=a.data
co=np.empty(len(me.vertices)*3); me.vertices.foreach_get('co',co); co=co.reshape(-1,3)
print("armref verts",len(co), co.min(0), co.max(0))
np.save("/tmp/claude-0/-home-user-kardonov-site/cb30cd45-1b88-5b9b-b3ff-480343f6cfce/scratchpad/out/cyber2/armco.npy",co)
s=bpy.data.objects["Sculpture_HiRes"].data
c2=np.empty(len(s.vertices)*3); s.vertices.foreach_get('co',c2); c2=c2.reshape(-1,3)
print("statue bbox", c2.min(0), c2.max(0))
