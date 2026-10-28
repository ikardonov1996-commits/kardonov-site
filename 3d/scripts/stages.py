# Carving stages: block -> S1 (very rough, faceted) -> S2 -> S3 -> S4 (smooth rough-out) -> final statue.
# Each stage = voxel remesh of the statue, decimated, pushed outward, then intersected with the
# previous stage, so every stage lies strictly inside the one before (material is only removed).
# usage: blender -b BLOCK.blend -P stages.py -- OUT.blend
import bpy, bmesh, sys, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index("--") + 1:]
out_path = argv[0]
sc = bpy.context.scene
statue = bpy.data.objects["Sculpture_HiRes"]; block = bpy.data.objects["Marble_Block"]
marble = bpy.data.materials["Marble"]

# name, voxel (m), target faces, outward offset (m), flat shading, polish
STAGES = [("Stage1", 0.030, 250, 0.014, True, 0.10),
          ("Stage2", 0.015, 1200, 0.008, True, 0.25),
          ("Stage3", 0.008, 6000, 0.0045, True, 0.45),
          ("Stage4", 0.004, 40000, 0.0022, False, 0.70)]

def select_only(o):
    for x in bpy.context.selected_objects: x.select_set(False)
    o.select_set(True); bpy.context.view_layer.objects.active = o

def inside_report(outer, inner, step=7):
    bvh = BVHTree.FromObject(outer, bpy.context.evaluated_depsgraph_get())
    co = np.empty(len(inner.data.vertices) * 3); inner.data.vertices.foreach_get('co', co); co = co.reshape(-1, 3)[::max(1, step if len(inner.data.vertices) > 5000 else 1)]
    out = 0
    for p in co:
        loc, nrm, i, d = bvh.find_nearest(Vector(p))
        if loc is None or (Vector(p) - loc).dot(nrm) > 0.0015: out += 1   # 1.5 mm tolerance (decimation)
    return out, len(co)

prev = block
for name, voxel, faces, offset, flat, polish in STAGES:
    old = bpy.data.objects.get(name)
    if old: bpy.data.objects.remove(old)
    ob = statue.copy(); ob.data = statue.data.copy(); ob.name = name; ob.data.name = name
    sc.collection.objects.link(ob); ob.modifiers.clear()
    select_only(ob)
    # 1) watertight coarse shell, inflated outward, re-remeshed so it stays a clean closed surface
    ob.data.remesh_voxel_size = voxel; ob.data.remesh_voxel_adaptivity = 0.0; bpy.ops.object.voxel_remesh()
    bm = bmesh.new(); bm.from_mesh(ob.data); bm.normal_update()
    for v in bm.verts: v.co += v.normal * offset
    bm.to_mesh(ob.data); bm.free()
    ob.data.remesh_voxel_size = voxel * 0.5; bpy.ops.object.voxel_remesh()
    bm = bmesh.new(); bm.from_mesh(ob.data)
    parts = bmesh.ops.split_edges(bm, edges=[]) and None
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:]); bm.to_mesh(ob.data); bm.free()
    # 2) carve from the previous stage (both closed manifolds -> robust boolean)
    keep = ob.data.copy()
    for solver in ('EXACT', 'FAST'):
        b = ob.modifiers.new("Inside", 'BOOLEAN'); b.operation = 'INTERSECT'; b.object = prev; b.solver = solver
        bpy.ops.object.modifier_apply(modifier=b.name)
        print('  %s boolean (%s): %d faces' % (name, solver, len(ob.data.polygons)))
        if len(ob.data.polygons) > 100: break
        ob.data = keep.copy()
    # 3) only now reduce to the target facet count
    ratio = min(1.0, faces / max(len(ob.data.polygons), 1))
    if ratio < 1.0:
        m = ob.modifiers.new("Dec", 'DECIMATE'); m.ratio = ratio; m.use_collapse_triangulate = True
        bpy.ops.object.modifier_apply(modifier=m.name)
    ob.data.polygons.foreach_set('use_smooth', [not flat] * len(ob.data.polygons))
    ob.data.materials.clear(); ob.data.materials.append(marble)
    ob["polish"] = polish; ob["gold"] = 0.0
    mw = ob.matrix_world.copy(); ob.parent = bpy.data.objects["Marble_Root"]; ob.matrix_world = mw
    o_out, o_n = inside_report(prev, ob)
    print("%s: %d faces, outside previous: %d/%d" % (name, len(ob.data.polygons), o_out, o_n))
    prev = ob

s_out, s_n = inside_report(prev, statue, step=11)
print("Statue vs Stage4: outside %d/%d" % (s_out, s_n))
bpy.ops.wm.save_as_mainfile(filepath=out_path, compress=True)
