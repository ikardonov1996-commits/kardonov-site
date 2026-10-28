# Check every sculpture vertex against the block, then render an x-ray view (block see-through).
import bpy, sys, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
argv = sys.argv[sys.argv.index("--") + 1:]
blk = bpy.data.objects["Marble_Block"]; st = bpy.data.objects["Sculpture_HiRes"]
bvh = BVHTree.FromObject(blk, bpy.context.evaluated_depsgraph_get())
co = np.empty(len(st.data.vertices) * 3); st.data.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
out, mind, worst = 0, 1.0, None
for p in co:
    loc, nrm, i, d = bvh.find_nearest(Vector(p))
    if (Vector(p) - loc).dot(nrm) >= 0: out += 1
    elif d < mind: mind, worst = d, p
print("ALL %d verts: outside=%d, min clearance %.1f mm at %s" % (len(co), out, mind * 1000, np.round(worst, 3)))
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading
sh.light = 'STUDIO'; sh.color_type = 'OBJECT'; sh.show_xray = True; sh.xray_alpha = 0.35
blk.color = (0.9, 0.85, 0.8, 1); st.color = (0.85, 0.35, 0.15, 1)
for o in bpy.data.objects:
    if o.name.startswith(("MarbleSwatch", "Floor")): o.hide_render = True
cam = sc.camera; cam.data.type = 'PERSP'; cam.data.lens = 70
for name, loc in (("front", (0.0, -3.4, 0.6)), ("side", (3.4, 0.0, 0.6))):
    cam.location = loc; d = Vector((0, 0, 0.56)) - cam.location; cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    sc.render.resolution_x = 600; sc.render.resolution_y = 800
    sc.render.filepath = argv[0] + "_" + name + ".png"; bpy.ops.render.render(write_still=True)
