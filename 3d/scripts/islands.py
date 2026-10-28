import bpy, sys, numpy as np
argv=sys.argv[sys.argv.index("--")+1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
me=bpy.data.objects["Sculpture_HiRes"].data
n=len(me.vertices)
ed=np.empty(len(me.edges)*2,np.int64); me.edges.foreach_get('vertices',ed); ed=ed.reshape(-1,2)
par=np.arange(n)
def find(x):
    r=x
    while par[r]!=r: r=par[r]
    while par[x]!=r: par[x],x=r,par[x]
    return r
for a,b in ed:
    ra,rb=find(a),find(b)
    if ra!=rb: par[ra]=rb
roots=np.array([find(i) for i in range(n)])
co=np.empty(n*3); me.vertices.foreach_get('co',co); co=co.reshape(-1,3)
u,c=np.unique(roots,return_counts=True)
print("components:",len(u))
for r,k in sorted(zip(u,c),key=lambda t:-t[1])[:25]:
    m=roots==r; print(k, np.round(co[m].min(0),3), np.round(co[m].max(0),3))
