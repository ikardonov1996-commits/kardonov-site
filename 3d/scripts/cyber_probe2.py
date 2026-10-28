import bpy, numpy as np
me=bpy.data.objects["Sculpture_HiRes"].data
co=np.empty(len(me.vertices)*3); me.vertices.foreach_get('co',co); co=co.reshape(-1,3)
np.save("/tmp/claude-0/-home-user-kardonov-site/cb30cd45-1b88-5b9b-b3ff-480343f6cfce/scratchpad/out/cyber/co.npy",co.astype(np.float32))
ed=np.empty(len(me.edges)*2,dtype=np.int64); me.edges.foreach_get('vertices',ed)
np.save("/tmp/claude-0/-home-user-kardonov-site/cb30cd45-1b88-5b9b-b3ff-480343f6cfce/scratchpad/out/cyber/edges.npy",ed.reshape(-1,2).astype(np.int32))
no=np.empty(len(me.vertices)*3); me.vertices.foreach_get('normal',no)
np.save("/tmp/claude-0/-home-user-kardonov-site/cb30cd45-1b88-5b9b-b3ff-480343f6cfce/scratchpad/out/cyber/no.npy",no.reshape(-1,3).astype(np.float32))
