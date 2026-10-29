import bpy, mathutils
from mathutils import Vector as V
p=V((-0.150,-0.028,0.455))
for o in bpy.data.objects:
    if o.type!='MESH': continue
    vis = not o.hide_render
    dg=bpy.context.evaluated_depsgraph_get(); oe=o.evaluated_get(dg)
    try:
        ok,loc,n,i=oe.closest_point_on_mesh(o.matrix_world.inverted()@p)
    except Exception as e: continue
    if ok:
        d=(o.matrix_world@loc-p).length
        if d<0.05: print("OBJ",o.name,vis,round(d,4),len(o.data.vertices))
