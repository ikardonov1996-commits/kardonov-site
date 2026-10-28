import bpy, numpy as np
me=bpy.data.objects["Sculpture_HiRes"].data
co=np.empty(len(me.vertices)*3); me.vertices.foreach_get('co',co); co=co.reshape(-1,3)
for z in np.arange(0.58,0.90,0.02):
    m=(co[:,0]>0.09)&(np.abs(co[:,2]-z)<0.005)
    if m.any(): P=co[m]; print("z=%.2f x[%.3f..%.3f] y[%.3f..%.3f] n=%d"%(z,P[:,0].min(),P[:,0].max(),P[:,1].min(),P[:,1].max(),m.sum()))
