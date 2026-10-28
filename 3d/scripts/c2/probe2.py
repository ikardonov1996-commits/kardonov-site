import bpy
from mathutils import Vector
o=bpy.data.objects["Robo_Collar_Gold"]
print(o.hide_render, o.hide_get(), o.users_collection, o.data.bevel_depth, [m.name for m in o.data.materials])
pts=[p.co for p in o.data.splines[0].points]; print(len(pts), pts[0], pts[len(pts)//2])
xs=[p.x for p in pts]; zs=[p.z for p in pts]; print(min(xs),max(xs),min(zs),max(zs))
