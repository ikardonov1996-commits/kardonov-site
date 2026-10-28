# Cheap EEVEE previews + vein-lock check.
# blender -b scene_rope_windlass.blend -P rope_preview.py -- <outdir> name:frame:cam[:engine] ...
import bpy, sys, math
import numpy as np
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
out = argv[0]; specs = argv[1:]
sc = bpy.context.scene; O = bpy.data.objects
sc.render.engine = "BLENDER_EEVEE_NEXT"
sc.eevee.taa_render_samples = 8
sc.render.film_transparent = False
sc.render.image_settings.file_format = "PNG"; sc.render.image_settings.color_mode = "RGB"
w = sc.world.node_tree.nodes["Background"]; w.inputs["Color"].default_value = (0.32, 0.33, 0.35, 1)
w.inputs["Strength"].default_value = 0.6

# ---- vein lock check: vertex in MarbleSpace coordinates at two frames ----
blk, msp = O["Marble_Block"], O["MarbleSpace"]
vids = [0, len(blk.data.vertices) // 2, len(blk.data.vertices) - 1]
res = []
for f in (1, 120, 240):
    sc.frame_set(f)
    M = msp.matrix_world.inverted() @ blk.matrix_world
    res.append([tuple(M @ blk.data.vertices[i].co) for i in vids])
    print("FRAME", f, "block world loc", tuple(round(x, 3) for x in blk.matrix_world.translation),
          "drum rot", round(O["Drum"].rotation_euler.x, 3), "pivot", tuple(round(x, 3) for x in O["Hang_Pivot"].matrix_world.translation),
          "descent", round(O["Descent_Control"]["descent"], 3))
print("VEIN_LOCK max diff", np.abs(np.array(res) - np.array(res[0])).max())

def mkcam(name, loc, tgt, lens):
    cd = bpy.data.cameras.new(name); cd.lens = lens; cd.clip_start = 0.02
    ob = bpy.data.objects.new(name, cd); sc.collection.objects.link(ob)
    ob.location = loc; ob.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return ob

for spec in specs:
    parts = spec.split(":"); name, f, cam = parts[0], int(parts[1]), parts[2]
    eng = parts[3] if len(parts) > 3 else "EEVEE"
    sc.frame_set(f)
    sc.render.engine = "BLENDER_WORKBENCH" if eng == "WB" else "BLENDER_EEVEE_NEXT"
    if cam == "main":
        sc.camera = O["Camera"]; sc.render.resolution_x, sc.render.resolution_y = 450, 800
    elif cam == "harness":
        p = O["Hang_Drop"].matrix_world.translation.copy()
        sc.camera = mkcam("cH", p + Vector((0.9, -2.0, 0.1)), p + Vector((0, 0, -0.75)), 50)
        sc.render.resolution_x, sc.render.resolution_y = 600, 800
    elif cam == "knot":
        p = O["Hang_Drop"].matrix_world.translation.copy()
        sc.camera = mkcam("cK", p + Vector((0.35, -0.6, 0.15)), p + Vector((0, 0, -0.15)), 50)
        sc.render.resolution_x, sc.render.resolution_y = 600, 600
    elif cam == "under":
        p = O["Hang_Drop"].matrix_world.translation.copy()
        sc.camera = mkcam("cU", p + Vector((1.2, -1.4, -2.6)), p + Vector((0, 0, -1.4)), 45)
        sc.render.resolution_x, sc.render.resolution_y = 600, 600
    elif cam == "windlass":
        sc.camera = mkcam("cW", (1.9, -2.6, 1.9), (0.1, 0, 0.85), 35)
        sc.render.resolution_x, sc.render.resolution_y = 800, 600
    sc.render.resolution_percentage = 100
    sc.render.filepath = "%s/%s.png" % (out, name)
    bpy.ops.render.render(write_still=True)
    print("RENDERED", name, flush=True)
