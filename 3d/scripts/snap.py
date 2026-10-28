# Quick viewport-style snapshots (EEVEE / Workbench) instead of full Cycles renders.
# usage: blender -b file.blend -P snap.py -- OUT_DIR engine(eevee|solid) view[,view...]
import bpy, sys
from mathutils import Vector
argv=sys.argv[sys.argv.index("--")+1:]
out, engine, views = argv[0], argv[1], argv[2].split(",")
sc=bpy.context.scene; cam=sc.camera
def look(o,t):
    d=Vector(t)-o.location; o.rotation_euler=d.to_track_quat('-Z','Y').to_euler()
VIEWS={ # name: (location, target, lens)
 "full":   ((1.0,-2.75,0.75),(0.08,0,0.5),85),
 "front":  ((0,-3.0,0.55),(0,0,0.5),85),
 "back":   ((0,3.0,0.55),(0,0,0.5),85),
 "left":   ((3.0,0,0.55),(0,0,0.5),85),
 "right":  ((-3.0,0,0.55),(0,0,0.5),85),
 "torso":  ((0.45,-1.6,0.85),(0.0,0,0.70),135),
 "belly":  ((0.12,-0.7,0.66),(-0.012,0,0.63),135),
 "pec":    ((-0.15,-0.7,0.76),(-0.08,0,0.74),135),
 "nipR":   ((-0.30,-0.55,0.80),(-0.079,-0.05,0.717),135),
 "nipL":   ((0.25,-0.58,0.81),(0.042,-0.05,0.738),135),
 "nipRc":  ((-0.13,-0.28,0.76),(-0.079,-0.05,0.717),135),
 "nipRs":  ((-0.33,-0.12,0.72),(-0.079,-0.05,0.717),135),
 "nipLc":  ((0.10,-0.30,0.78),(0.042,-0.05,0.738),135),
 "face":   ((0.10,-0.75,0.90),(0.0,0,0.895),135),
 "hand":   ((0.30,-0.55,0.85),(0.07,-0.05,0.78),135),
 "blk":    ((1.3,-3.3,0.95),(0.0,0,0.56),70),
 "blkb":   ((-1.6,2.9,1.10),(0.0,0,0.56),70),
 "blkc":   ((0.55,-1.25,1.05),(0.12,-0.1,0.85),70),
 "head":   ((0.25,-1.0,0.92),(0.0,0,0.90),135),
}
if engine=="solid":
    sc.render.engine='BLENDER_WORKBENCH'; sh=sc.display.shading
    sh.light='STUDIO'; sh.color_type='SINGLE'; sh.single_color=(0.8,0.78,0.75); sh.show_cavity=True
else:
    # engine "eevee" = fast check (8 samples, 600x800); "eeveehq" = cleaner preview (32, 900x1200)
    sc.render.engine='BLENDER_EEVEE_NEXT'; sc.eevee.taa_render_samples=32 if engine=="eeveehq" else 8
fast = engine!="eeveehq"
sc.render.resolution_x=600 if fast else 900; sc.render.resolution_y=800 if fast else 1200
for o in bpy.data.objects:
    if o.name.startswith("MarbleSwatch"): o.hide_render=True
for v in views:
    loc,t,lens=VIEWS[v]; cam.data.type='PERSP'; cam.location=loc; look(cam,t); cam.data.lens=lens
    sc.render.filepath="%s/snap_%s_%s.png"%(out,engine,v); bpy.ops.render.render(write_still=True)
