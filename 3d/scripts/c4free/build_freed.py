# Stage C4_Freed, rebuilt: rough faceted figure (unchanged) in front of a THICK block remnant.
# Modelled on unfinished marbles (Michelangelo's Prisoners / St Matthew, Rodin's Hand of God):
#   * the remnant is a mass of the stage-2 block (C1), not a sheet: its back / right / left faces and the
#     pitched top slope of C1 are kept as they were, so continuity reads across stages;
#   * everything new is cut by planes (pitching tool): front faces, stepped top, chamfered arrises,
#     a lower ledge behind the legs, a side wing still holding the hanging arm, a roughly pitched base;
#   * convex arrises get faceted conchoidal chips / stepped spalls (convex-hull cutters, not round bites);
#   * a pointed/drilled trench (~3 cm wide, 3.5 cm deep) runs round the figure where it meets the stone,
#     its floor parallel to the face it is cut into; the deepest parts of the figure stay attached;
#   * tool marks as small inward displacement only: point furrows + claw combs on worked planes, point pits
#     on the base top and in the trench, ragged pitch steps on broken faces; original C1 faces untouched.
# Every boolean is volume-validated. Figure mesh is copied verbatim from the backup (anim_carving_v2.blend).
# usage: blender -b anim_carving.blend -P build_freed.py -- OUT.blend [BACKUP.blend]
import bpy, bmesh, sys, os, numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index("--") + 1:]
out_path = argv[0]
backup = argv[1] if len(argv) > 1 else os.path.join(os.path.dirname(bpy.data.filepath), "anim_carving_v2.blend")
sc = bpy.context.scene; O = bpy.data.objects
statue = O["Sculpture_HiRes"]; block = O["Marble_Block"]; root = O["Marble_Root"]; C1 = O["C1_Pitched"]
C4 = O["C4_Freed"]
VOXEL = 0.002
rng = np.random.default_rng(41)
for o in list(O):
    if o.name.startswith(("TMP_", "FIG_")): O.remove(o)

# ------------------------------------------------------------------ helpers
def select_only(o):
    for x in bpy.context.selected_objects: x.select_set(False)
    o.select_set(True); bpy.context.view_layer.objects.active = o
def vol(ob):
    b_ = bmesh.new(); b_.from_mesh(ob.data); v = b_.calc_volume(signed=True); b_.free(); return abs(v)
def holes(ob):
    bm = bmesh.new(); bm.from_mesh(ob.data); n = sum(1 for e in bm.edges if not e.is_manifold); bm.free(); return n
def mk(name, bm):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); sc.collection.objects.link(ob); return ob
def dup(src, name):
    ob = src.copy(); ob.data = src.data.copy(); ob.name = name; ob.data.name = name
    sc.collection.objects.link(ob); ob.modifiers.clear(); ob.animation_data_clear(); ob.parent = None
    ob.matrix_world = Matrix.Identity(4); return ob
def boolean(ob, other, op, self_=False, tries=5):
    """Boolean with volume + manifold check; on failure the cutter is nudged by <0.5 mm and retried."""
    jr = np.random.default_rng(7)
    for k in range(tries):
        if k:
            dv = Vector(jr.uniform(-0.0004, 0.0004, 3)); other.data.transform(Matrix.Translation(dv))
        try:
            return _boolean(ob, other, op, self_)
        except RuntimeError:
            if k == tries - 1: raise
def _boolean(ob, other, op, self_=False):
    va, vb = vol(ob), vol(other)
    for solver in ('EXACT', 'FAST'):
        t = ob.copy(); t.data = ob.data.copy(); sc.collection.objects.link(t)
        select_only(t); m = t.modifiers.new("B", 'BOOLEAN'); m.operation = op; m.object = other; m.solver = solver
        if solver == 'EXACT': m.use_self = self_; m.use_hole_tolerant = True
        bpy.ops.object.modifier_apply(modifier=m.name)
        v = vol(t)
        ok = (op == 'INTERSECT' and 1e-5 < v <= min(va, vb) * 1.002) or \
             (op == 'UNION' and max(va, vb) * 0.999 < v <= (va + vb) * 1.002) or \
             (op == 'DIFFERENCE' and 1e-5 < v <= va * 1.0001 and v >= va - vb * 1.002)
        print('   %s %s(%s,%s): va=%.5f vb=%.5f v=%.5f faces=%d holes=%d %s' % (op, solver, ob.name, other.name, va, vb, v,
              len(t.data.polygons), holes(t), 'ok' if ok else 'REJECT'), flush=True)
        if ok and holes(t) == 0:
            ob.data = t.data; ob.data.name = ob.name; O.remove(t); return v
        O.remove(t)
    raise RuntimeError("boolean failed: %s %s %s" % (ob.name, op, other.name))
def keep_largest(ob):
    nm = ob.name
    bm_ = bmesh.new(); bm_.from_mesh(ob.data)                     # FAST booleans leave stray loose verts/edges
    bmesh.ops.delete(bm_, geom=[v for v in bm_.verts if not v.link_faces], context='VERTS')
    bm_.to_mesh(ob.data); bm_.free()
    select_only(ob); bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.separate(type='LOOSE'); bpy.ops.object.mode_set(mode='OBJECT')
    parts = list(bpy.context.selected_objects); big = max(parts, key=vol)
    for o in parts:
        if o is not big: O.remove(o)
    big.name = nm; big.data.name = nm
    return big, len(parts) - 1
def remesh(ob, voxel):
    select_only(ob); ob.data.remesh_voxel_size = voxel; ob.data.remesh_voxel_adaptivity = 0.0; bpy.ops.object.voxel_remesh()
def inflate(ob, d):
    bm = bmesh.new(); bm.from_mesh(ob.data); bm.normal_update()
    for v in bm.verts: v.co += v.normal * d
    bm.to_mesh(ob.data); bm.free()
def decimate(ob, faces):
    r = min(1.0, faces / max(len(ob.data.polygons), 1))
    if r >= 1.0: return
    backup_ = ob.data.copy(); select_only(ob)
    m = ob.modifiers.new("D", 'DECIMATE'); m.ratio = r; m.use_collapse_triangulate = True
    bpy.ops.object.modifier_apply(modifier=m.name)
    if holes(ob) > 0: ob.data = backup_; print("   decimate opened holes on %s -> kept" % ob.name)
def pl(n, p):
    """plane keeping n.x <= n.p (n outward)."""
    n = Vector(n).normalized(); return (n, n.dot(Vector(p)))

# ------------------------------------------------------------------ C1 as a clean low-poly convex solid
bm = bmesh.new()
for v in C1.data.vertices: bm.verts.new(v.co)
bmesh.ops.convex_hull(bm, input=bm.verts[:])
bmesh.ops.dissolve_limit(bm, angle_limit=0.035, verts=bm.verts[:], edges=bm.edges[:])
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
C1_PLANES = [(f.normal.copy(), f.normal.dot(f.verts[0].co)) for f in bm.faces if f.calc_area() > 0.002]
C1low = mk("TMP_C1low", bm)
print("C1 hull faces", len(C1low.data.polygons), "vol %.4f" % vol(C1low))

PLANES = []          # (n, d, class) for every cut -> tool-mark class lookup later
_k = [0]
def piece(name, planes, cls):
    """C1 (enlarged a little, by a different amount per piece so no two pieces share a coplanar face -> clean
    exact unions) cut by planes; the union is intersected with the true C1 afterwards."""
    bm = bmesh.new(); bm.from_mesh(C1low.data); _k[0] += 1
    sc_ = 1.03 + 0.013 * _k[0]
    bmesh.ops.scale(bm, vec=(sc_, sc_, sc_), space=Matrix.Translation((0, 0, -0.58)), verts=bm.verts[:])
    for n, d in planes:
        res = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=n * d, plane_no=n, clear_outer=True)
        cut = [e for e in res['geom_cut'] if isinstance(e, bmesh.types.BMEdge)]
        if cut: bmesh.ops.contextual_create(bm, geom=cut)
        PLANES.append((n, d, cls))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    ob = mk(name, bm); print("  piece %s vol %.4f faces %d holes %d" % (name, vol(ob), len(ob.data.polygons), holes(ob)))
    return ob
def yfront(y0, ax=0.0, az=0.0, x0=0.0, z0=0.5):
    """keep y >= y0 + ax(x-x0) + az(z-z0)"""
    n = Vector((ax, -1.0, az)); return pl(n, (x0, y0, z0))
def ztop(z0, ax=0.0, ay=0.0, x0=0.0, y0=0.15):
    """keep z <= z0 + ax(x-x0) + ay(y-y0)"""
    n = Vector((-ax, -ay, 1.0)); return pl(n, (x0, y0, z0))

# ------------------------------------------------------------------ the remnant, as plane-cut pieces of C1
# (block axes: figure faces -y, camera is front-right; back face y=+0.248 and side faces x=+-0.31 are C1's)
A = piece("TMP_A", [          # main slab behind the torso: two front planes meeting in a blunt vertical ridge
    yfront(0.088, ax=-0.10, az=-0.015),
    yfront(0.100, ax=0.22, az=0.02, x0=0.05),
    ztop(0.800, ax=0.25, ay=0.55, x0=0.0),                      # broken top, falls to the left, faces the viewer
    ztop(0.955, ax=-0.20, ay=0.35, x0=0.15),                    # second break plane over the right half
    pl((0.30, -0.55, 0.78), (0.0, 0.10, 0.815)),                # front-top arris chamfered by a big spall
    pl((0.55, -0.80, 0.0), (0.285, 0.13, 0.5)),                 # front-right vertical arris pitched off
    pl((-0.72, -0.62, 0.30), (-0.285, 0.10, 0.6)),              # front-left vertical arris pitched off
], 'pitch')
Bp = piece("TMP_B", [         # back-right remnant: keeps C1's original pitched top slope up to ~0.9-1.0
    yfront(0.150, ax=0.10),
    pl((-1.0, -0.25, 0.10), (0.125, 0.15, 0.85)),               # its inner (left) broken face
    pl((0.35, -0.80, 0.45), (0.27, 0.15, 0.93)),                # chamfered front-top corner
    pl((-0.55, -0.20, 0.81), (0.14, 0.15, 0.905)),              # its top-left peak knocked off
], 'pitch')
W = piece("TMP_W", [          # side wing still holding the hanging right arm / thigh (viewer's left)
    yfront(0.035, ax=-0.25, az=0.05, x0=-0.2),
    pl((1.0, -0.10, 0.18), (-0.150, 0.0, 0.40)),                # inner face, cut back toward the figure
    ztop(0.560, ax=0.55, ay=0.30, x0=-0.2, y0=0.05),            # top, broken, sloping down outward
    pl((-0.75, -0.66, 0.0), (-0.255, 0.02, 0.4)),               # outer front arris pitched
], 'point')
L = piece("TMP_L", [          # lower ledge behind / between the legs (worked front-to-back, still deep)
    yfront(0.050, ax=0.05, az=0.10, z0=0.2),
    ztop(0.200, ax=-0.15, ay=0.45, x0=0.0, y0=0.05),
    pl((0.62, -0.78, 0.05), (0.255, 0.04, 0.2)),
    pl((0.0, -0.45, 0.89), (0.0, 0.05, 0.175)),                   # chamfer on the ledge's front-top arris
], 'point')
# base: roughly pitched block round the plinth (polish only at the last stage)
BASE_TOP = 0.118
Bs = piece("TMP_Base", [
    ztop(BASE_TOP, ax=0.04, ay=-0.05, x0=0.03, y0=0.0),
    yfront(-0.192, ax=0.05, az=0.10, z0=0.05),
    pl((1.0, -0.06, 0.12), (0.247, 0.0, 0.05)),
    pl((-1.0, 0.05, 0.10), (-0.170, 0.0, 0.05)),
    pl((0.70, -0.70, 0.12), (0.225, -0.172, 0.05)),              # chamfered front-right corner
    pl((-0.70, -0.70, 0.10), (-0.153, -0.175, 0.05)),            # chamfered front-left corner
    pl((0.0, -0.60, 0.80), (0.0, -0.180, BASE_TOP)),             # front-top arris pitched
    pl((0.62, -0.30, 0.73), (0.235, -0.10, BASE_TOP)),           # right-top arris pitched
], 'base')

stone = A
for p in (Bp, W, L, Bs):
    boolean(stone, p, 'UNION')
stone.name = "TMP_Stone"
boolean(stone, C1low, 'INTERSECT')            # back to the true C1 faces (sides, back, pitched top slope)
v_union = vol(stone)
ADD = {"A": A, "B": Bp, "W": W, "L": L}

# ------------------------------------------------------------------ chips and stepped spalls along convex arrises
def hull_ob(name, pts):
    bm = bmesh.new()
    for p in pts: bm.verts.new(p)
    bmesh.ops.convex_hull(bm, input=bm.verts[:])
    for v in [v for v in bm.verts if not v.link_faces]: bm.verts.remove(v)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return bm
bm = bmesh.new(); bm.from_mesh(stone.data); bm.normal_update()
cand = []
for e in bm.edges:
    if len(e.link_faces) != 2 or not e.is_convex: continue
    f1, f2 = e.link_faces
    ang = f1.normal.angle(f2.normal)
    if ang < 0.35: continue
    a_, b_ = e.verts[0].co, e.verts[1].co
    mid = (a_ + b_) / 2
    if min(a_.z, b_.z) < 0.004: continue                       # standing on the floor
    if mid.y > 0.235: continue                                 # back arrises (unseen, original block)
    cand.append((e.calc_length() * (0.5 if mid.z > 0.75 else 1.0), a_.copy(), b_.copy(), f1.normal.copy(), f2.normal.copy()))
bm.free()
cbm = bmesh.new(); nchips = 0
for length, a_, b_, n1, n2 in cand:
    k = int(length / 0.11 + rng.uniform(0, 1))
    ed = (b_ - a_).normalized()
    for _ in range(k):
        t = rng.uniform(0.04, 0.96); p = a_ + (b_ - a_) * t
        Lc = rng.uniform(0.035, 0.11); h = Lc * rng.uniform(0.09, 0.17)
        w1, w2 = rng.uniform(0.5, 1.5), rng.uniform(0.5, 1.5)      # asymmetric: bites more into one face
        m = (n1 * w1 + n2 * w2).normalized()
        side = (n1 - n2).normalized()
        deep = p - m * h + ed * rng.uniform(-0.2, 0.2) * Lc
        pts = [p + ed * Lc * 0.5 + m * 0.001, p - ed * Lc * 0.5 + m * 0.001, deep,
               p + ed * Lc * rng.uniform(0.1, 0.3) - m * h * rng.uniform(0.80, 0.95) + side * h * rng.uniform(-0.4, 0.4),
               p - ed * Lc * rng.uniform(0.1, 0.3) - m * h * rng.uniform(0.80, 0.95) + side * h * rng.uniform(-0.4, 0.4),
               p + ed * Lc * 0.55 + m * 0.03, p - ed * Lc * 0.55 + m * 0.03,
               p + n1 * 0.03 + ed * Lc * 0.3, p + n2 * 0.03 - ed * Lc * 0.3, p + m * 0.05]
        hb = hull_ob("chip", pts); me = bpy.data.meshes.new("c"); hb.to_mesh(me); hb.free()
        cbm.from_mesh(me); bpy.data.meshes.remove(me); nchips += 1
        # stepped spall: sometimes a second, smaller, deeper chip nested in the first
        if rng.uniform() < 0.35:
            Lc2 = Lc * 0.45; h2 = h * 1.35; q = p + ed * rng.uniform(-0.25, 0.25) * Lc
            pts2 = [q + ed * Lc2 * 0.5 + m * 0.001, q - ed * Lc2 * 0.5 + m * 0.001, q - m * h2,
                    q + ed * Lc2 * 0.55 + m * 0.03, q - ed * Lc2 * 0.55 + m * 0.03, q + m * 0.04,
                    q + n1 * 0.02, q + n2 * 0.02]
            hb = hull_ob("chip2", pts2); me = bpy.data.meshes.new("c"); hb.to_mesh(me); hb.free()
            cbm.from_mesh(me); bpy.data.meshes.remove(me); nchips += 1
Chips = mk("TMP_Chips", cbm)
print("chips:", nchips, "on", len(cand), "arrises")
CHIP_BVH = BVHTree.FromObject(Chips, bpy.context.evaluated_depsgraph_get())
select_only(Chips); bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.separate(type='LOOSE'); bpy.ops.object.mode_set(mode='OBJECT')
chip_obs = list(bpy.context.selected_objects); applied = 0
import builtins
_print = builtins.print
for c in chip_obs:                                  # one at a time: a cutter that breaks the mesh is skipped
    builtins.print = lambda *a, **k: None
    try: boolean(stone, c, 'DIFFERENCE', tries=2); applied += 1
    except RuntimeError: pass
    finally: builtins.print = _print
    O.remove(c)
print("chips applied %d/%d, stone vol %.5f faces %d holes %d" % (applied, len(chip_obs), vol(stone), len(stone.data.polygons), holes(stone)))

# ------------------------------------------------------------------ trench round the figure
if C4.get("c4_version", 1) == 1:                 # still the original stage: take the figure from it directly
    oldme = C4.data.copy()
else:                                             # already rebuilt: original stage from the backup file
    with bpy.data.libraries.load(backup, link=False) as (src, dst):
        dst.meshes = ["C4_Freed"]
    oldme = dst.meshes[0]                         # figure = its small loose part
FIG = bpy.data.objects.new("FIG_src", oldme); sc.collection.objects.link(FIG)
select_only(FIG); bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.separate(type='LOOSE'); bpy.ops.object.mode_set(mode='OBJECT')
parts = list(bpy.context.selected_objects)
fig = min(parts, key=lambda o: len(o.data.vertices))
for o in parts:
    if o is not fig: O.remove(o)
fig.name = "FIG_figure"; print("figure verts", len(fig.data.vertices), "vol %.4f" % vol(fig))

Fi = dup(statue, "TMP_Finf"); remesh(Fi, 0.022); inflate(Fi, 0.016 + 0.032); remesh(Fi, 0.011); decimate(Fi, 700)
print("inflated figure faces", len(Fi.data.polygons), "holes", holes(Fi))
TRENCH = 0.035
for nm, pc in ADD.items():                       # channel floor = each face it is cut into, set back 3.5 cm
    sh = dup(pc, "TMP_sh_" + nm); sh.data.transform(Matrix.Translation((0, TRENCH, 0)))
    try: boolean(Fi, sh, 'DIFFERENCE')
    except RuntimeError: print("   (no overlap with", nm, ")")
    O.remove(sh)
for n, d, c in list(PLANES):
    if c in ('pitch', 'point') and n.y < -0.5:
        PLANES.append((n, d + n.dot(Vector((0, TRENCH, 0))), 'trench'))
bsh = dup(Bs, "TMP_bsh"); boolean(Fi, bsh, 'DIFFERENCE'); O.remove(bsh)
v0 = vol(stone)
boolean(stone, Fi, 'DIFFERENCE')
print("trench removed %.5f m3" % (v0 - vol(stone)))
stone, nloose = keep_largest(stone)
print("dropped loose fragments:", nloose, "stone vol %.5f" % vol(stone), flush=True)
STONE_LOW = dup(stone, "TMP_StoneLow")
for o in list(O):
    if o.name.startswith("TMP_") and o.name not in (stone.name, STONE_LOW.name): O.remove(o)

# ------------------------------------------------------------------ dense surface + tool marks
remesh(stone, VOXEL)
print("remeshed stone faces", len(stone.data.polygons))
low_bvh = BVHTree.FromObject(STONE_LOW, bpy.context.evaluated_depsgraph_get())
lowN = [p.normal.copy() for p in STONE_LOW.data.polygons]
lowC = [p.center.copy() for p in STONE_LOW.data.polygons]

def classify(n, c):
    if CHIP_BVH.find_nearest(c)[3] is not None and CHIP_BVH.find_nearest(c)[3] < 0.0008: return 'chip'
    for N_, d_ in C1_PLANES:
        if n.dot(N_) > 0.999 and abs(N_.dot(c) - d_) < 0.0015: return 'orig'
    best = None
    for N_, d_, cl in PLANES:
        if n.dot(N_) > 0.999 and abs(N_.dot(c) - d_) < 0.0015: best = cl
    return best or 'channel'
cls_of = [classify(n, c) for n, c in zip(lowN, lowC)]
from collections import Counter; print("low face classes", Counter(cls_of))

co = np.empty(len(stone.data.vertices) * 3); stone.data.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
nv = len(co); fidx = np.zeros(nv, int); fdist = np.zeros(nv)
for i in range(nv):
    loc, nr, fi, dd = low_bvh.find_nearest(Vector(co[i])); fidx[i] = fi; fdist[i] = dd
# C1 is not exactly convex (natural quarry break on the back-left): snap anything outside C1 back onto it
c1_bvh = BVHTree.FromObject(C1, bpy.context.evaluated_depsgraph_get())
snapped = np.zeros(nv, bool)
for i in range(nv):
    loc, nr, fi, dd = c1_bvh.find_nearest(Vector(co[i]))
    if loc is not None and (Vector(co[i]) - loc).dot(nr) > 0.0002:
        co[i] = loc[:]; snapped[i] = True
print("snapped onto C1:", snapped.sum())
FN = np.array([n[:] for n in lowN]); FC = np.array([c[:] for c in lowC])
CL = np.array(cls_of)
vn = FN[fidx]; vcls = CL[fidx]

def h01(*a):
    h = np.zeros_like(a[0], dtype=np.int64)
    for k, x in zip((73856093, 19349663, 83492791, 2654435761), a):
        h = h ^ (x.astype(np.int64) * k)
    h = (h ^ (h >> 13)) * 1274126177; h = h ^ (h >> 16)
    return (h & 0xFFFFFF).astype(np.float64) / float(0xFFFFFF)
# tangent basis per vertex from its low face normal
up = np.where(np.abs(vn[:, 2:3]) > 0.9, np.array([[1.0, 0, 0]]), np.array([[0, 0, 1.0]]))
t1 = np.cross(up, vn); t1 /= np.linalg.norm(t1, axis=1, keepdims=True); t2 = np.cross(vn, t1)
U = (co * t1).sum(1); Vv = (co * t2).sum(1); fs = fidx.astype(np.int64)

def patches(cell, base_ang, spread):
    """Voronoi patches (jittered grid in the face plane): stroke direction and phase per patch."""
    gi = np.floor(U / cell).astype(np.int64); gj = np.floor(Vv / cell).astype(np.int64)
    best = np.full(nv, 1e9); ang = np.zeros(nv); ph = np.zeros(nv); pid = np.zeros(nv)
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            ci, cj = gi + di, gj + dj
            cx = (ci + h01(ci, cj, fs, 1 + 0 * ci)) * cell; cy = (cj + h01(ci, cj, fs, 2 + 0 * ci)) * cell
            d2 = (U - cx) ** 2 + (Vv - cy) ** 2
            m = d2 < best; best[m] = d2[m]
            a = base_ang + (h01(ci, cj, fs, 3 + 0 * ci) - 0.5) * 2 * spread
            ang[m] = a[m]; ph[m] = h01(ci, cj, fs, 4 + 0 * ci)[m]; pid[m] = h01(ci, cj, fs, 5 + 0 * ci)[m]
    return ang, ph, pid
base_ang = h01(fs, fs, fs, fs) * np.pi
def furrows(lam, depth, cell, spread, stroke):
    ang, ph, pid = patches(cell, base_ang, spread)
    s = U * np.cos(ang) + Vv * np.sin(ang); al = -U * np.sin(ang) + Vv * np.cos(ang)
    w = s / lam + ph; row = np.floor(w).astype(np.int64); w = w - row
    g = np.clip(1 - np.abs(w - 0.5) / 0.28, 0, 1) ** 1.3                      # V groove
    rid = (pid * 1e4).astype(np.int64)
    sl = stroke * (0.6 + 1.2 * h01(row, rid, fs, 17 + 0 * row))               # every furrow its own stroke length
    e = al / sl + h01(row, rid, fs, 6 + 0 * row); e = e - np.floor(e)
    env = np.clip(np.sin(np.pi * e) * 4.0, 0, 1) * (0.55 + 0.45 * h01(row, rid, fs, 7 + 0 * row))
    return depth * g * env
def claw(lam, depth, cell, spread, stroke):
    ang, ph, pid = patches(cell, base_ang + 0.6, spread)
    s = U * np.cos(ang) + Vv * np.sin(ang); al = -U * np.sin(ang) + Vv * np.cos(ang)
    band = np.floor(s / (lam * 6) + ph).astype(np.int64)                     # one stroke of the claw = 5 teeth
    w = s / lam; w = w - np.floor(w)
    g = (0.5 - 0.5 * np.cos(2 * np.pi * w)) ** 2
    e = al / stroke + h01(band, (pid * 1e4).astype(np.int64), fs, 8 + 0 * band); e = e - np.floor(e)
    env = np.clip(np.sin(np.pi * e) * 3.0, 0, 1) * (h01(band, (pid * 1e4).astype(np.int64), fs, 9 + 0 * band) > 0.3)
    return depth * g * env
def pits(cell, depth, prob, r0, r1):
    gi = np.floor(U / cell).astype(np.int64); gj = np.floor(Vv / cell).astype(np.int64)
    out = np.zeros(nv)
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            ci, cj = gi + di, gj + dj
            cx = (ci + h01(ci, cj, fs, 11 + 0 * ci)) * cell; cy = (cj + h01(ci, cj, fs, 12 + 0 * ci)) * cell
            a = h01(ci, cj, fs, 13 + 0 * ci) * np.pi; r = r0 + (r1 - r0) * h01(ci, cj, fs, 14 + 0 * ci)
            dx, dy = U - cx, Vv - cy
            pa = (dx * np.cos(a) + dy * np.sin(a)) / (r * 1.8); pb = (-dx * np.sin(a) + dy * np.cos(a)) / r
            q = np.clip(1 - (pa * pa + pb * pb), 0, 1) ** 0.7
            on = h01(ci, cj, fs, 15 + 0 * ci) < prob
            out = np.maximum(out, depth * q * on * (0.6 + 0.4 * h01(ci, cj, fs, 16 + 0 * ci)))
    return out
def pitch_steps(depth):
    """ragged pitched face: shallow conchoidal ripples / steps running across the break."""
    ang, ph, pid = patches(0.07, base_ang + 1.3, 0.35)
    s = U * np.cos(ang) + Vv * np.sin(ang)
    w = s / 0.022 + ph * 3; w = w - np.floor(w)
    return depth * w ** 2.2

D = np.zeros(nv)
m = vcls == 'pitch'
D[m] = (pitch_steps(0.0024) + 0.6 * furrows(0.010, 0.0010, 0.06, 0.6, 0.05) + pits(0.016, 0.0013, 0.35, 0.0022, 0.0035))[m]
m = vcls == 'point'
D[m] = (furrows(0.009, 0.0009, 0.06, 0.5, 0.05) + 0.5 * claw(0.0045, 0.0006, 0.09, 0.4, 0.12) + pits(0.013, 0.0011, 0.4, 0.002, 0.0032))[m]
m = vcls == 'base'
D[m] = (pits(0.011, 0.0017, 0.75, 0.0022, 0.0038) + 0.5 * furrows(0.011, 0.0012, 0.05, 0.6, 0.04))[m]
m = (vcls == 'channel') | (vcls == 'trench')
D[m] = (pits(0.010, 0.0018, 0.8, 0.002, 0.0035) + 0.5 * furrows(0.008, 0.0014, 0.04, 0.8, 0.03))[m]
m = vcls == 'chip'
D[m] = 0.0006 * (0.5 - 0.5 * np.cos(2 * np.pi * (U / 0.009 + 0.3 * np.sin(Vv / 0.013))))[m]   # faint conchoidal rings
D[snapped] = 0.0
co2 = co - vn * D[:, None]
stone.data.vertices.foreach_set('co', co2.ravel()); stone.data.update()
print("tool marks: mean depth %.5f max %.5f" % (D.mean(), D.max()))

# ------------------------------------------------------------------ shading, attributes, join figure, swap into C4_Freed
select_only(stone); bpy.ops.object.shade_smooth_by_angle(angle=0.55)
_blk = BVHTree.FromObject(block, bpy.context.evaluated_depsgraph_get())
names = ("fracture", "joint", "joint_rim")
src = {nm: np.empty(len(block.data.vertices)) for nm in names}
for nm in names: block.data.attributes[nm].data.foreach_get('value', src[nm])
poly_v = [tuple(p.vertices) for p in block.data.polygons]
outa = {nm: np.zeros(len(stone.data.vertices)) for nm in names}
for i, v in enumerate(stone.data.vertices):
    loc, nrm, fi, dist = _blk.find_nearest(v.co)
    if loc is not None and dist < 0.002:
        vi = list(poly_v[fi])
        for nm in names: outa[nm][i] = src[nm][vi].mean()
for nm in names:
    if nm in stone.data.attributes: stone.data.attributes.remove(stone.data.attributes[nm])
    a_ = stone.data.attributes.new(nm, 'FLOAT', 'POINT'); a_.data.foreach_set('value', outa[nm])
for a_ in [a_.name for a_ in fig.data.attributes if a_.name not in names and not a_.name.startswith('.')
           and a_.name not in ('position', 'sharp_face', 'sharp_edge')]:
    fig.data.attributes.remove(fig.data.attributes[a_])
mat = bpy.data.materials["Marble_Carve"]
stone.data.materials.clear(); stone.data.materials.append(mat)
fig.data.materials.clear(); fig.data.materials.append(mat)
for x in bpy.context.selected_objects: x.select_set(False)
stone.select_set(True); fig.select_set(True); bpy.context.view_layer.objects.active = stone
bpy.ops.object.join()
newme = stone.data; newme.name = "C4_Freed_v2"
oldmesh = C4.data; C4.data = newme
if oldmesh.users == 0: bpy.data.meshes.remove(oldmesh)
O.remove(stone)
for o in list(O):
    if o.name.startswith(("TMP_", "FIG_")): O.remove(o)
for me in list(bpy.data.meshes):
    if me.users == 0: bpy.data.meshes.remove(me)
C4["c4_version"] = 2
print("C4_Freed: %d faces, open edges %d" % (len(C4.data.polygons), holes(C4)))

# ------------------------------------------------------------------ nesting: C5 inside new C4, new C4 inside C1
def outside(outer, inner, tol=0.002, n=4000):
    bvh = BVHTree.FromObject(outer, bpy.context.evaluated_depsgraph_get())
    c_ = np.empty(len(inner.data.vertices) * 3); inner.data.vertices.foreach_get('co', c_); c_ = c_.reshape(-1, 3)
    c_ = c_[rng.choice(len(c_), min(n, len(c_)), replace=False)]
    bad = 0
    for p in c_:
        loc, nr, i, dd = bvh.find_nearest(Vector(p))
        if loc is None or (Vector(p) - loc).dot(nr) > tol: bad += 1
    return bad, len(c_)
print("nest C4_Freed in C1_Pitched outside %d/%d" % outside(C1, C4))
print("nest C5_Point in C4_Freed outside %d/%d" % outside(C4, O["C5_Point"]))
bpy.ops.wm.save_as_mainfile(filepath=out_path, compress=True)
print("FREED OK", out_path)
