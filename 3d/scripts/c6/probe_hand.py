import bpy, numpy as np
D=bpy.data
for o in D.objects: print("OBJ",o.name,o.type,len(o.data.vertices) if o.type=='MESH' else '', tuple(round(x,3) for x in o.location), tuple(round(x,3) for x in o.scale), o.parent.name if o.parent else None)
a=D.objects["ArmRef"]; me=a.data; co=np.zeros(len(me.vertices)*3); me.vertices.foreach_get("co",co); co=co.reshape(-1,3)
M=np.array(a.matrix_world); co=co@M[:3,:3].T+M[:3,3]
np.save("/tmp/claude-0/-home-user-kardonov-site/cb30cd45-1b88-5b9b-b3ff-480343f6cfce/scratchpad/scripts/c6/armref_co.npy",co)
h=co[co[:,2]<0.52]; print("hand bbox",h.min(0),h.max(0),len(h))
for z in np.arange(0.52,0.36,-0.005):
    s=co[np.abs(co[:,2]-z)<0.0012]
    if len(s): print("z %.3f n %d x[%.3f %.3f] y[%.3f %.3f]"%(z,len(s),s[:,0].min(),s[:,0].max(),s[:,1].min(),s[:,1].max()))
