# Find the raised (fist) hand: front-most points in the box where the fist is, report centre.
import bpy, sys, numpy as np
me=bpy.data.objects["Sculpture_HiRes"].data
co=np.empty(len(me.vertices)*3); me.vertices.foreach_get('co',co); co=co.reshape(-1,3)
m=(co[:,0]>0.03)&(co[:,0]<0.13)&(co[:,2]>0.72)&(co[:,2]<0.84)&(co[:,1]<-0.02)
P=co[m]; print("FIST bbox", P.min(0).round(3), P.max(0).round(3), "centre", P.mean(0).round(3))
m=(co[:,0]<-0.12)&(co[:,2]>0.38)&(co[:,2]<0.52)
P=co[m]; print("LOW HAND bbox", P.min(0).round(3), P.max(0).round(3), "centre", P.mean(0).round(3))
