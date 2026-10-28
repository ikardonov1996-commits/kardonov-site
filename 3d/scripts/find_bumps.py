import bpy, sys, numpy as np
from mathutils.kdtree import KDTree
argv=sys.argv[sys.argv.index("--")+1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
me=bpy.data.objects["Sculpture_HiRes"].data
n=len(me.vertices)
co=np.empty(n*3,np.float32); me.vertices.foreach_get('co',co); co=co.reshape(-1,3)
no=np.empty(n*3,np.float32); me.vertices.foreach_get('normal',no); no=no.reshape(-1,3)
print("bbox",co.min(0),co.max(0))
sel=np.where((co[:,2]>0.40)&(co[:,2]<0.85)&(no[:,1]<-0.2))[0]
kd=KDTree(n)
for i,c in enumerate(co): kd.insert(c,i)
kd.balance()
cand=sel[::8]
prot=np.zeros(len(cand))
for k,i in enumerate(cand):
    idx=[j for _,j,_ in kd.find_range(co[i],0.018)]
    m=co[idx].mean(0); prot[k]=np.dot(co[i]-m,no[i])
order=np.argsort(-np.abs(prot))
picked=[]
for k in order:
    p=co[cand[k]]
    if any(np.linalg.norm(p-q)<0.03 for q,_ in picked): continue
    picked.append((p,prot[k]))
    if len(picked)>=14: break
for p,v in picked: print("PEAK %.4f %.4f %.4f  prot=%.5f"%(p[0],p[1],p[2],v))
