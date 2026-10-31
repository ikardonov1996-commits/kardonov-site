import bpy
from mathutils import Vector as V
from bpy_extras.object_utils import world_to_camera_view as w2c
sc=bpy.context.scene; O=bpy.data.objects; cam=sc.camera
print("CAM", cam.location[:], cam.data.lens)
fr=list(sc["stage_frames"]); ALL=["Marble_Block","C1_Pitched","C3_Relief2","C4_Freed","C5_Point","C6_Claw","Sculpture_HiRes"]
for n in ["C5_Point","C6_Claw","Sculpture_HiRes"]:
    sc.frame_set(fr[ALL.index(n)]); o=O[n]
    bb=[o.matrix_world@V(c) for c in o.bound_box]
    print("BB",n,[round(min(p[i] for p in bb),3) for i in range(3)],[round(max(p[i] for p in bb),3) for i in range(3)])
    dg=bpy.context.evaluated_depsgraph_get()
    # sample: ray from camera through image points -> hit location
    import numpy as np
    for (x,y) in [(0.46,0.72),(0.46,0.70),(0.47,0.68),(0.47,0.58),(0.47,0.55),(0.47,0.52),(0.50,0.55),(0.44,0.55)]:
        fr_=cam.data.view_frame(scene=sc); # corners in cam space
        tr,br,bl,tl=fr_[0],fr_[1],fr_[2],fr_[3]
        p=bl+(br-bl)*x+(tl-bl)*y; d=(cam.matrix_world@p-cam.location).normalized()
        for m in ALL: O[m].hide_set(m!=n)
        hit=sc.ray_cast(dg,cam.location,d)
        print(" ",n,(x,y),hit[0], tuple(round(v,3) for v in hit[1]) if hit[0] else None, hit[4].name if hit[0] else None, tuple(round(v,2) for v in hit[2]) if hit[0] else None)
