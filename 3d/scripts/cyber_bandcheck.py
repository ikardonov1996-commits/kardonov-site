import bpy, math, numpy as np
from mathutils.bvhtree import BVHTree
sc=bpy.data.objects["Sculpture_HiRes"]; b=bpy.data.objects["Neuro_Band"]
dg=bpy.context.evaluated_depsgraph_get()
bvh=BVHTree.FromObject(sc,dg)
me=b.data; mw=b.matrix_world
vs=[mw@v.co for v in me.vertices]
# inner ring = verts index%4 in (0,3)
out=[]
for i in range(0,len(vs),4):
    for k in (0,3):
        p=vs[i+k]; loc,n,idx,d=bvh.find_nearest(p)
        # inside test: sign via normal
        s=1 if (p-loc).dot(n)>0 else -1
        out.append((i//4,k,s*d))
a=np.array(out)
for seg in range(0,180,10):
    r=a[a[:,0]==seg]; print("seg %3d ang %4d gap(mm) %s"%(seg,-180+seg*2+1, np.round(r[:,2]*1000,1)))
print("gap stats mm: min %.1f median %.1f max %.1f"%(a[:,2].min()*1000,np.median(a[:,2])*1000,a[:,2].max()*1000))
