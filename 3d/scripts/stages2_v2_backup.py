# Carving stages modelled on real practice (pitching tool -> point chisel relief, front to back ->
# freed rough figure -> claw -> flat chisel -> rasp -> polish).
#   C1  block with big masses pitched off where the figure isn't (planar cuts, wide clearance)
#   C2  relief 1/3: the rough figure is cut in from the front down to depth d1, the rest is still block
#   C3  relief 2/3
#   C4  figure freed, a slab of stone left behind it
#   C5..C7  faceted -> refined -> smooth rough-out (all sides), each inside the block
#   final   the polished statue (asset, untouched)
# usage: blender -b asset_all.blend -P stages2.py -- OUT.blend
import bpy, bmesh, sys, numpy as np
from mathutils import Vector, Matrix, noise as mnoise
from mathutils.kdtree import KDTree
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index("--") + 1:]
out_path = argv[0]
sc = bpy.context.scene; O = bpy.data.objects
statue = O["Sculpture_HiRes"]; block = O["Marble_Block"]; root = O["Marble_Root"]
marble = bpy.data.materials["Marble"]
rng = np.random.default_rng(5)
for o in list(O):
    if o.name.startswith(("Stage", "C_", "TMP_")): O.remove(o)

P = np.empty(len(statue.data.vertices) * 3); statue.data.vertices.foreach_get('co', P); P = P.reshape(-1, 3)[::5]
CAM = np.array([1.35, -3.6]); VIEW = np.array([*(CAM / np.linalg.norm(CAM)), 0.0])   # horizontal direction to camera
depth = -(P @ VIEW)                                   # 0 = front-most point of the figure, grows to the back
d_lo, d_hi = depth.min(), depth.max()

def select_only(o):
    for x in bpy.context.selected_objects: x.select_set(False)
    o.select_set(True); bpy.context.view_layer.objects.active = o
def dup(src, name):
    ob = src.copy(); ob.data = src.data.copy(); ob.name = name; ob.data.name = name
    sc.collection.objects.link(ob); ob.modifiers.clear(); ob.parent = None; ob.matrix_world = src.matrix_world.copy()
    return ob
def vol(ob):
    b_ = bmesh.new(); b_.from_mesh(ob.data); v = b_.calc_volume(signed=True); b_.free(); return abs(v)
def boolean(ob, other, op):
    """Boolean with sanity check on volume; for INTERSECT also tries the operands swapped."""
    va, vb = vol(ob), vol(other)
    keep = ob.data.copy()
    tries = [(ob, other, s_) for s_ in ('EXACT', 'FAST')]
    if op == 'INTERSECT': tries += [(other, ob, s_) for s_ in ('EXACT', 'FAST')]
    for tgt, opd, solver in tries:
        t = tgt.copy(); t.data = (keep if tgt is ob else tgt.data).copy(); sc.collection.objects.link(t); t.modifiers.clear()
        select_only(t); m = t.modifiers.new("B", 'BOOLEAN'); m.operation = op; m.object = (opd if opd is not ob else ob); m.solver = solver
        if opd is ob: ob.data = keep
        bpy.ops.object.modifier_apply(modifier=m.name)
        v = vol(t)
        ok = (op == 'INTERSECT' and 1e-4 < v <= min(va, vb) * 1.002) or (op == 'UNION' and v > max(va, vb) * 1.001) \
             or (op == 'DIFFERENCE' and 1e-4 < v < va * 0.999)
        if ok:
            ob.data = t.data.copy(); ob.data.name = ob.name; O.remove(t); return solver
        O.remove(t)
    raise RuntimeError("boolean failed: %s %s" % (ob.name, op))
def remesh(ob, voxel):
    select_only(ob); ob.data.remesh_voxel_size = voxel; ob.data.remesh_voxel_adaptivity = 0.0; bpy.ops.object.voxel_remesh()
def inflate(ob, d):
    bm = bmesh.new(); bm.from_mesh(ob.data); bm.normal_update()
    for v in bm.verts: v.co += v.normal * d
    bm.to_mesh(ob.data); bm.free()
def holes(ob):
    bm = bmesh.new(); bm.from_mesh(ob.data); n = sum(1 for e in bm.edges if not e.is_manifold); bm.free(); return n
def decimate(ob, faces):
    r = min(1.0, faces / max(len(ob.data.polygons), 1))
    if r >= 1.0: return
    backup = ob.data.copy(); select_only(ob)
    m = ob.modifiers.new("D", 'DECIMATE'); m.ratio = r; m.use_collapse_triangulate = True
    bpy.ops.object.modifier_apply(modifier=m.name)
    if holes(ob) > 0: ob.data = backup; print("   decimate opened holes on %s -> kept undecimated" % ob.name)
def box(name, centre, normal, size=3.0):
    """Big box whose face passes through `centre` with outward normal `normal` (keeps the side behind it)."""
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=size)
    n = Vector(normal).normalized(); rot = n.to_track_quat('Z', 'Y').to_matrix().to_4x4()
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); sc.collection.objects.link(ob)
    ob.matrix_world = Matrix.Translation(Vector(centre) + n * size / 2) @ rot   # box lies on the +normal side
    return ob
def finish(ob, polish, flat, sub=False):
    ob.data.polygons.foreach_set('use_smooth', [not flat] * len(ob.data.polygons))
    ob.data.materials.clear(); ob.data.materials.append(marble)
    ob["polish"] = polish; ob["gold"] = 0.0
    mw = ob.matrix_world.copy(); ob.parent = root; ob.matrix_world = mw
    print("%s: %d faces, open edges %d" % (ob.name, len(ob.data.polygons), holes(ob)))

def backing(name, d, seed):
    """Stone left behind a relief: a hacked, uneven surface at depth ~d (not a plane).
    Deeper trench right around the emerging figure, rising toward the untouched block further out."""
    Uh = np.array([-VIEW[1], VIEW[0], 0.0]); Z = np.array([0, 0, 1.0])
    em = P[depth < d + 0.02]                                    # parts of the figure already in front
    kd = KDTree(len(em))
    for i, p in enumerate(em): kd.insert((p @ Uh, p @ Z, 0.0), i)
    kd.balance()
    off = Vector((seed * 13.1, seed * 7.7, seed * 3.3))
    nu, nw = 200, 280; us = np.linspace(-0.45, 0.45, nu); ws = np.linspace(-0.05, 1.25, nw)
    bm = bmesh.new(); grid = []
    for w in ws:
        row = []
        for u in us:
            q = Vector((u, w, 0.0)) + off
            _, _, dist = kd.find((u, w, 0.0))
            h = 0.014 * mnoise.noise(q * 3.5)                                         # broad undulation
            h += 0.012 * round(mnoise.noise(q * 2.2 + Vector((5, 5, 5))) * 3) / 3      # stepped terraces (layers taken off)
            ang = 0.7 + 0.6 * mnoise.noise(q * 2.0 + Vector((9, 1, 4)))                # furrow direction drifts by patch
            fu = u * np.cos(ang) + w * np.sin(ang); fw = -u * np.sin(ang) + w * np.cos(ang)
            h += 0.005 * abs(mnoise.noise(Vector((fu * 70.0, fw * 9.0, seed * 0.37))))  # point-chisel furrows
            h += 0.0015 * mnoise.noise(q * 120.0)                                      # grit
            h -= 0.040 * max(0.0, 1.0 - dist / 0.09) ** 1.5                            # trench round the figure
            h += 0.035 * min(1.0, max(0.0, (dist - 0.12) / 0.20))                      # rises toward the block
            row.append(bm.verts.new(Vector(u * Uh + w * Z + VIEW * (-d + h))))
        grid.append(row)
    for j in range(nw - 1):
        for i in range(nu - 1):
            bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
    ext = bmesh.ops.extrude_face_region(bm, geom=bm.faces[:])
    for v in [g for g in ext['geom'] if isinstance(g, bmesh.types.BMVert)]: v.co -= Vector(VIEW * 0.8)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); sc.collection.objects.link(ob)
    return ob

# ---- rough figure for the relief stages: chunky point-chisel mass (voxel 30 mm, +16 mm)
R = dup(statue, "TMP_R"); remesh(R, 0.030); inflate(R, 0.016); remesh(R, 0.012)
decimate(R, 3500)                                          # point-chisel planes, not a smooth blob

# ---- C1: pitch off big masses with planes that stay well clear (>= 45 mm) of the figure
C1 = dup(block, "C1_Pitched")
bm = bmesh.new(); bm.from_mesh(C1.data)
cuts = 0
for _ in range(400):
    if cuts >= 7: break
    nrm = rng.normal(size=3); nrm[2] = abs(nrm[2]) * rng.uniform(0.1, 0.6); nrm /= np.linalg.norm(nrm)
    if nrm @ VIEW < -0.5: continue                       # don't open the back yet
    c = (P @ nrm).max() + rng.uniform(0.06, 0.10)
    vco = np.array([v.co[:] for v in bm.verts])
    if (vco @ nrm).max() - c < 0.03: continue             # would barely touch the block
    res = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=Vector(nrm * c), plane_no=Vector(nrm), clear_outer=True)
    bmesh.ops.contextual_create(bm, geom=[e for e in res['geom_cut'] if isinstance(e, bmesh.types.BMEdge)])
    cuts += 1
bm.to_mesh(C1.data); bm.free()
C1raw = dup(C1, "TMP_C1raw")            # ~30-face convex block: robust boolean partner
remesh(C1, 0.004)
print("C1 pitch cuts:", cuts)
finish(C1, 0.0, False)

# ---- C2..C4: relief, cut from the front down to depth d (stone behind d untouched)
for name, frac in (("C2_Relief1", 0.33), ("C3_Relief2", 0.62), ("C4_Freed", 0.86)):
    d = d_lo + frac * (d_hi - d_lo)
    B = backing("TMP_Box", d, int(frac * 100))                  # hacked stone surface behind the relief
    A = dup(C1raw, "TMP_A"); boolean(A, B, 'INTERSECT'); O.remove(B)    # stone kept behind the relief
    Rc = dup(R, "TMP_Rc"); boolean(Rc, C1raw, 'INTERSECT')               # rough figure, clipped to the block
    for x in bpy.context.selected_objects: x.select_set(False)
    A.select_set(True); Rc.select_set(True); bpy.context.view_layer.objects.active = A
    bpy.ops.object.join()                                                 # overlapping solids ...
    S = A; S.name = name; S.data.name = name
    remesh(S, 0.004)                                                      # ... voxel remesh = their union
    select_only(S); bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.separate(type='LOOSE'); bpy.ops.object.mode_set(mode='OBJECT')
    parts = [o for o in bpy.context.selected_objects]; big = max(parts, key=vol)
    for o in parts:
        if o is not big: O.remove(o)                                      # drop floating chips
    S = big; S.name = name; S.data.name = name
    print("   %s: kept main piece, dropped %d loose fragments" % (name, len(parts) - 1))
    finish(S, 0.0, False)

# ---- C5..C7: freed figure refined on all sides, each cut out of the block
for name, voxel, faces, off, flat, pol in (("C5_Point", 0.022, 900, 0.010, True, 0.12),
                                           ("C6_Claw", 0.010, 5000, 0.005, True, 0.35),
                                           ("C7_Rasp", 0.004, 60000, 0.0022, False, 0.70)):
    S = dup(statue, name); remesh(S, voxel); inflate(S, off); remesh(S, voxel * 0.5)
    boolean(S, block, 'INTERSECT'); decimate(S, faces)
    finish(S, pol, flat)
O.remove(R); O.remove(C1raw)

# ---- nesting check (sampled): each stage vs the one before, statue vs C7
def outside(outer, inner, tol=0.002, n=4000):
    bvh = BVHTree.FromObject(outer, bpy.context.evaluated_depsgraph_get())
    co = np.empty(len(inner.data.vertices) * 3); inner.data.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
    co = co[rng.choice(len(co), min(n, len(co)), replace=False)]
    bad = 0
    for p in co:
        loc, nr, i, dd = bvh.find_nearest(Vector(p))
        if loc is None or (Vector(p) - loc).dot(nr) > tol: bad += 1
    return bad, len(co)
order = ["Marble_Block", "C1_Pitched", "C2_Relief1", "C3_Relief2", "C4_Freed", "C5_Point", "C6_Claw", "C7_Rasp", "Sculpture_HiRes"]
for a, b in zip(order, order[1:]):
    print("nest %-12s in %-12s outside %d/%d" % ((b, a) + outside(O[a], O[b])))
bpy.ops.wm.save_as_mainfile(filepath=out_path, compress=True)
print("STAGES OK")
