import bpy, bmesh
from mathutils import Vector as V
from mathutils.bvhtree import BVHTree
P0 = V((-0.108, 0, 0.70)); NCUT = V((-0.994, 0, 0.108)).normalized()
c=bpy.data.objects["Robo_Core"]; bm=bmesh.new(); bm.from_mesh(c.data)
be=[e for e in bm.edges if e.is_boundary]
print("boundary edges", len(be))
zs=sorted(set(round(v.co.z,2) for e in be for v in e.verts)); print(zs[:3], zs[-3:])
dc=[(v.co-P0).dot(NCUT) for e in be for v in e.verts]; print("dcut range", min(dc), max(dc))
# marble near the top of shoulder: which side of the plane is the torso surface at the top?
s=bpy.data.objects["Sculpture_HiRes"]
dg=bpy.context.evaluated_depsgraph_get(); bvh=BVHTree.FromObject(s,dg)
for y in (0.0,0.02,0.04,0.06):
    loc,n,i,d=bvh.ray_cast(V((-0.115,y,0.9)),V((0,0,-1)),0.3)
    print("marble top at y",y,loc, (loc-P0).dot(NCUT) if loc else None)
cb=BVHTree.FromObject(c,dg)
for y in (0.0,0.02,0.04,0.06):
    loc,n,i,d=cb.ray_cast(V((-0.115,y,0.9)),V((0,0,-1)),0.3); print("core top",y,loc)
