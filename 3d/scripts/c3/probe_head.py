import bpy, math
from mathutils import Vector as V
from mathutils.bvhtree import BVHTree
s=bpy.data.objects["Sculpture_HiRes"]; print(s.matrix_world)
dg=bpy.context.evaluated_depsgraph_get(); bvh=BVHTree.FromObject(s,dg)
HC=V((-0.031,-0.002,0)); fa=math.atan2(-0.59,0.81)
for off in (0,30,60,80,90,100,120,150,180,-30,-60,-80,-90,-100,-120,-150):
    th=fa+math.radians(off); d=V((math.cos(th),math.sin(th),0)); row=[]
    for z in [0.90+0.005*i for i in range(18)]:
        o=HC+V((0,0,z))+d*0.2; loc,n,i,dd=bvh.ray_cast(o,-d,0.2)
        row.append("%.1f"%((0.2-dd)*1000) if loc else "--")
    print("%4d"%off," ".join(row))
print("z:"," ".join("%.3f"%(0.90+0.005*i) for i in range(18)))
# top of head
for dx in (-0.02,0,0.02):
    loc,n,i,dd=bvh.ray_cast(HC+V((dx,0,1.2)),V((0,0,-1)),0.5); print("top",dx,loc)
