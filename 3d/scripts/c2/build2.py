# Cyber David v2: rebuild robotic arm (layered plates, mechanics, glow, articulated hand) and the neuro headband.
# Run on asset_statue_cyber_v1.blend:  blender -b asset_statue_cyber_v1.blend -P build2.py -- STAGE_CUT.blend OUT.blend
import bpy, bmesh, sys, math, time
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index("--") + 1:]
STAGE, OUT = argv[0], argv[1]
T0 = time.time()
def log(*a): print("[c2 %.1fs]" % (time.time() - T0), *a, flush=True)
V = Vector
D = bpy.data; SC = bpy.context.scene
SCULPT = D.objects["Sculpture_HiRes"]
COL = D.collections.get("Cyber")

# ------------------------------------------------------------------ cleanup old parts
KEEP = set()
for o in list(D.objects):
    if o.name.startswith(("Robo_", "Neuro_")) and o.name not in KEEP:
        D.objects.remove(o, do_unlink=True)
for coll in (D.meshes, D.curves):
    for m in list(coll):
        if m.users == 0: coll.remove(m)

with D.libraries.load(STAGE) as (src, dst):
    dst.objects = ["ArmRef"]
ARMREF = dst.objects[0]; SC.collection.objects.link(ARMREF)

# ------------------------------------------------------------------ skeleton
P0 = V((-0.108, 0, 0.70)); NCUT = V((-0.994, 0, 0.108)).normalized()
S = V((-0.128, 0.032, 0.765)); E = V((-0.151, 0.046, 0.625)); W = V((-0.175, -0.002, 0.502))
H = V((-0.180, -0.006, 0.455))
u1 = (E - S).normalized(); u2 = (W - E).normalized(); u3 = (H - W).normalized()
L0 = (E - S).length; L1 = (W - E).length
nEl = (u1 + u2).normalized(); nWr = (u2 + u3).normalized()
def sd(p, pt, n): return (p - pt).dot(n)
d_cut = lambda p: sd(p, P0, NCUT)

def seg(k):
    a, u, L = (S, u1, L0) if k == 0 else (E, u2, L1)
    lat = V((-1, 0, 0)); lat = (lat - u * lat.dot(u)).normalized()
    fr = lat.cross(u).normalized()
    return a, u, lat, fr, L

# ------------------------------------------------------------------ materials
def mat(name, base, metal=0.0, rough=0.4, coat=0.0, emis=None, estr=0.0, vp=None):
    m = D.materials.get(name) or D.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*base, 1)
    b.inputs["Metallic"].default_value = metal
    b.inputs["Roughness"].default_value = rough
    b.inputs["Coat Weight"].default_value = coat
    b.inputs["Coat Roughness"].default_value = 0.22
    if emis:
        b.inputs["Emission Color"].default_value = (*emis, 1)
        b.inputs["Emission Strength"].default_value = estr
    else:
        b.inputs["Emission Strength"].default_value = 0.0
    m.diffuse_color = (*(vp or base), 1)
    return m

M_IVORY = mat("Cyber_Ivory", (0.62, 0.47, 0.29), rough=0.36, coat=0.3)
M_GOLD = mat("Cyber_Gold", (0.95, 0.66, 0.30), metal=1.0, rough=0.28)
M_GUN = mat("Cyber_Gunmetal", (0.10, 0.105, 0.12), metal=0.9, rough=0.33)
M_DARK = mat("Cyber_Rubber", (0.025, 0.027, 0.03), rough=0.55)
M_STEEL = mat("Cyber_Steel", (0.55, 0.57, 0.6), metal=1.0, rough=0.2)
M_BLUE = mat("Cyber_GlowBlue", (0.05, 0.40, 1.0), rough=0.3, emis=(0.02, 0.30, 1.0), estr=3.0, vp=(0.25, 0.66, 1.0))
M_BLUE_HOT = mat("Cyber_GlowBlueHot", (0.2, 0.6, 1.0), rough=0.3, emis=(0.03, 0.34, 1.0), estr=6.0, vp=(0.5, 0.8, 1.0))
M_NGOLD = mat("Neuro_Gold", (1.0, 0.58, 0.20), metal=1.0, rough=0.28)
M_AMBER = mat("Neuro_GlowAmber", (1.0, 0.35, 0.02), rough=0.3, emis=(1.0, 0.42, 0.04), estr=6.0, vp=(1.0, 0.6, 0.2))
M_RING = mat("Neuro_GlowRing", (1.0, 0.4, 0.05), rough=0.3, emis=(1.0, 0.32, 0.02), estr=9.0, vp=(1.0, 0.5, 0.1))
M_LENS = mat("Neuro_Lens", (0.9, 0.6, 0.3), metal=0.3, rough=0.12, emis=(1.0, 0.40, 0.08), estr=2.5)

# ------------------------------------------------------------------ helpers
def link(ob):
    (COL or SC.collection).objects.link(ob)
    ob.parent = SCULPT; ob.matrix_parent_inverse = SCULPT.matrix_world.inverted()
    return ob

def finish_mesh(me, smooth_angle=40):
    me.shade_smooth()
    try: me.set_sharp_from_angle(angle=math.radians(smooth_angle))
    except Exception: pass

class Acc:
    def __init__(s, name, mats):
        s.name, s.mats = name, mats; s.V = []; s.F = []; s.M = []
    def add_bm(s, bm, mtx, mi=0):
        off = len(s.V)
        s.V += [tuple(mtx @ v.co) for v in bm.verts]
        bm.verts.index_update()
        for f in bm.faces:
            s.F.append([off + v.index for v in f.verts]); s.M.append(mi)
        bm.free()
    def build(s, angle=40):
        me = D.meshes.new(s.name); me.from_pydata(s.V, [], s.F)
        for m in s.mats: me.materials.append(m)
        me.polygons.foreach_set("material_index", s.M); me.update()
        finish_mesh(me, angle)
        return link(D.objects.new(s.name, me))

def frame(loc, z, yhint=V((0, 0, 1))):
    z = z.normalized()
    if abs(z.dot(yhint.normalized())) > 0.95: yhint = V((1, 0, 0)) if abs(z.x) < 0.9 else V((0, 1, 0))
    x = yhint.cross(z).normalized(); y = z.cross(x)
    m = Matrix((x, y, z)).transposed().to_4x4(); m.translation = loc
    return m

def bm_cube(dx, dy, dz, bev=0.0, segs=3):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts: v.co = V((v.co.x * dx, v.co.y * dy, v.co.z * dz))
    if bev > 0:
        bmesh.ops.bevel(bm, geom=list(bm.edges) + list(bm.verts), offset=bev, segments=segs, profile=0.5, affect='EDGES', clamp_overlap=True)
    return bm

def bm_cyl(r, h, segs=24, bev=0.0, r2=None):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segs, radius1=r, radius2=r if r2 is None else r2, depth=h)
    if bev > 0:
        ed = [e for e in bm.edges if abs(e.verts[0].co.z - e.verts[1].co.z) < 1e-9 and abs(abs(e.verts[0].co.z) - h / 2) < 1e-9]
        bmesh.ops.bevel(bm, geom=ed, offset=bev, segments=2, profile=0.5, affect='EDGES', clamp_overlap=True)
    return bm

def bm_sphere(r, u=16, v=10):
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=u, v_segments=v, radius=r); return bm

def bm_torus(R, r, nu=40, nv=10):
    bm = bmesh.new(); rows = []
    for i in range(nu):
        a = 2 * math.pi * i / nu; ca, sa = math.cos(a), math.sin(a); row = []
        for j in range(nv):
            b = 2 * math.pi * j / nv
            rr = R + r * math.cos(b)
            row.append(bm.verts.new((rr * ca, rr * sa, r * math.sin(b))))
        rows.append(row)
    for i in range(nu):
        for j in range(nv):
            a, b = rows[i], rows[(i + 1) % nu]
            bm.faces.new((a[j], b[j], b[(j + 1) % nv], a[(j + 1) % nv]))
    return bm

def tube_obj(name, pts, radius, m, closed=False, res=3):
    cu = D.curves.new(name, 'CURVE'); cu.dimensions = '3D'
    sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1)
    for p, q in zip(sp.points, pts): p.co = (*q, 1)
    sp.use_cyclic_u = closed
    cu.bevel_depth = radius; cu.bevel_resolution = res; cu.use_fill_caps = True
    cu.materials.append(m)
    return link(D.objects.new(name, cu))

def smooth_pts(pts, it=3, closed=False):
    P = np.array([tuple(p) for p in pts])
    for _ in range(it):
        if closed: P = (np.roll(P, 1, 0) + 2 * P + np.roll(P, -1, 0)) / 4
        else: P[1:-1] = (P[:-2] + 2 * P[1:-1] + P[2:]) / 4
    return [V(p) for p in P]

def apply_mods(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    me = D.meshes.new_from_object(ob.evaluated_get(dg))
    old = ob.data; ob.modifiers.clear(); ob.data = me; D.meshes.remove(old)

# ------------------------------------------------------------------ 1. reference surfaces
log("remesh")
bm = bmesh.new(); bm.from_mesh(ARMREF.data)
bmesh.ops.holes_fill(bm, edges=[e for e in bm.edges if e.is_boundary], sides=0)
bm.to_mesh(ARMREF.data); bm.free()
m = ARMREF.modifiers.new("rm", 'REMESH'); m.mode = 'VOXEL'; m.voxel_size = 0.0011
apply_mods(ARMREF)

def layer_copy(name, it, fac, disp):
    ob = D.objects.new(name, ARMREF.data.copy()); SC.collection.objects.link(ob)
    if it:
        m = ob.modifiers.new("lap", 'LAPLACIANSMOOTH'); m.iterations = it; m.lambda_factor = fac
        m.use_volume_preserve = True; m.use_normalized = True
    if disp:
        m = ob.modifiers.new("d", 'DISPLACE'); m.strength = disp; m.mid_level = 0.0; m.direction = 'NORMAL'
    apply_mods(ob); return ob

SMOOTH = layer_copy("tmp_smooth", 14, 0.6, 0.0)
SBVH = BVHTree.FromObject(SMOOTH, bpy.context.evaluated_depsgraph_get())

# core (gunmetal body visible in gaps): 2 mm inside the marble, open at shoulder cut, cut at the wrist
CORE = layer_copy("Robo_Core", 5, 0.4, -0.0022)
bm = bmesh.new(); bm.from_mesh(CORE.data)
bmesh.ops.bisect_plane(bm, geom=list(bm.faces) + list(bm.edges) + list(bm.verts), dist=1e-7, plane_co=P0 + NCUT * 0.0010, plane_no=NCUT, clear_inner=True)
kill = [f for f in bm.faces if sd(f.calc_center_median(), W + u2 * 0.002, nWr) > 0]
bmesh.ops.delete(bm, geom=kill, context='FACES')
bm.to_mesh(CORE.data); bm.free()
CORE.data.materials.append(M_GUN); finish_mesh(CORE.data, 60)
SC.collection.objects.unlink(CORE); link(CORE)
# collar: angular sampling of core + marble outlines at the shoulder plane
CB0 = BVHTree.FromObject(CORE, bpy.context.evaluated_depsgraph_get())
MB0 = BVHTree.FromObject(SCULPT, bpy.context.evaluated_depsgraph_get())
ce1 = V((0, 1, 0)); ce1 = (ce1 - NCUT * ce1.dot(NCUT)).normalized(); ce2 = NCUT.cross(ce1).normalized()
C0 = S + NCUT * (-(S - P0).dot(NCUT))          # shoulder joint projected onto the plane
NA = 200; RC = np.zeros(NA); RM = np.full(NA, np.nan)
for i in range(NA):
    a_ = 2 * math.pi * i / NA; dv = ce1 * math.cos(a_) + ce2 * math.sin(a_)
    loc, n_, k_, dd = CB0.ray_cast(C0 + NCUT * 0.0016, dv, 0.08); RC[i] = dd if loc is not None else np.nan
    loc, n_, k_, dd = MB0.ray_cast(C0 - NCUT * 0.0008, dv, 0.08); RM[i] = dd if loc is not None else np.nan
RC = np.where(np.isnan(RC), np.nanmedian(RC), RC); RM = np.where(np.isnan(RM), RC + 0.002, RM)
RR_ = np.maximum(RC + 0.0018, np.minimum(RM, RC + 0.004))
for _ in range(6): RR_ = np.maximum(RR_, (np.roll(RR_, 1) + 2 * RR_ + np.roll(RR_, -1)) / 4)
for _ in range(8): RR_ = (np.roll(RR_, 1) + 2 * RR_ + np.roll(RR_, -1)) / 4
CL = [C0 + NCUT * 0.0006 + (ce1 * math.cos(2 * math.pi * i / NA) + ce2 * math.sin(2 * math.pi * i / NA)) * RR_[i] for i in range(NA)]
CLC = C0
log("collar loop", len(CL))
CBVH = BVHTree.FromObject(CORE, bpy.context.evaluated_depsgraph_get())
log("core done")

def radial(k, t, th):
    a, u, lat, fr, L = seg(k)
    A = a + u * t; d = lat * math.cos(th) + fr * math.sin(th)
    loc, n, i, dist = SBVH.ray_cast(A, d, 0.12)
    return A, d, (dist if loc is not None else float('nan'))

def surf_pt(k, t, th, off):
    A, d, r = radial(k, t, th)
    return A + d * (r + off), d

# ------------------------------------------------------------------ 2. plates
LAY = [0.0032, 0.0058, 0.0085]; THK = 0.0022
def fill_nan(R):
    m = np.isnan(R)
    if m.any(): R[m] = np.nanmedian(R)
    return R

def grid_smooth(R, it):
    Q = R.copy()
    for _ in range(it):
        P = np.pad(Q, 1, mode='edge')
        Q = (P[:-2, 1:-1] + P[2:, 1:-1] + P[1:-1, :-2] + P[1:-1, 2:] + 4 * Q) / 8
    return Q

def build_plate(name, ray_fn, sizes, off, dome=0.0012, roll=0.0007, sm=4, trim_rows=2, thick=THK, post=None):
    """ray_fn(x, y) -> (origin, dir, dist) for x,y in [-1,1] (already rounded-rect mapped)"""
    nu = max(12, int(sizes[0] / 0.0011)); nv = max(8, int(sizes[1] / 0.0011))
    nu += nu % 2; nv += nv % 2
    xs = np.linspace(-1, 1, nu + 1); ys = np.linspace(-1, 1, nv + 1)
    O = {}; R = np.zeros((nu + 1, nv + 1)); RHO = np.zeros_like(R)
    for i, x in enumerate(xs):
        for j, y in enumerate(ys):
            mx = max(abs(x), abs(y)); n4 = (x ** 4 + y ** 4) ** 0.25
            sx, sy = (x * mx / n4, y * mx / n4) if n4 > 0 else (0.0, 0.0)
            o, d, r = ray_fn(sx, sy); O[i, j] = (o, d); R[i, j] = r; RHO[i, j] = mx
    R = fill_nan(R)
    Rs = np.maximum(grid_smooth(R, sm), R - 0.0006)
    ss = np.clip((RHO - 0.82) / 0.18, 0, 1); ss = ss * ss * (3 - 2 * ss)
    RR = Rs + off + dome * (1 - RHO ** 2) - roll * ss
    bm = bmesh.new(); vg = {}
    for i in range(nu + 1):
        for j in range(nv + 1):
            o, d = O[i, j]; p = o + d * RR[i, j]
            if post: p = post(p)
            vg[i, j] = bm.verts.new(p)
    for i in range(nu):
        for j in range(nv):
            f = bm.faces.new((vg[i, j], vg[i + 1, j], vg[i + 1, j + 1], vg[i, j + 1]))
            edge = (i < trim_rows or j < trim_rows or i >= nu - trim_rows or j >= nv - trim_rows)
            f.material_index = 1 if edge else 0
    bm.normal_update()
    o, d = O[nu // 2, nv // 2]
    fc = [f for f in bm.faces if f.material_index == 0]
    if sum(f.normal.dot(d) for f in fc) < 0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
    me = D.meshes.new(name); bm.to_mesh(me); bm.free()
    me.materials.append(M_IVORY); me.materials.append(M_GOLD)
    finish_mesh(me, 70)
    ob = link(D.objects.new(name, me))
    m = ob.modifiers.new("solid", 'SOLIDIFY'); m.thickness = thick; m.offset = -1.0
    m.use_rim = True; m.material_offset_rim = 1; m.use_even_offset = True
    m = ob.modifiers.new("bev", 'BEVEL'); m.width = 0.00045; m.segments = 2; m.limit_method = 'ANGLE'
    m.angle_limit = math.radians(50)
    return ob, O, RR

def arm_plate(name, k, t0, t1, th0, th1, layer, **kw):
    th0, th1 = math.radians(th0), math.radians(th1)
    a, u, lat, fr, L = seg(k)
    def fn(x, y):
        t = t0 + (t1 - t0) * (x + 1) / 2; th = th0 + (th1 - th0) * (y + 1) / 2
        return radial(k, t, th)
    rmean = 0.024
    return build_plate(name, fn, (t1 - t0, rmean * (th1 - th0)), LAY[layer], **kw)[0]

PL = []
# pauldron: spherical cap around the shoulder joint
PA = V((-1, 0.04, 0.62)).normalized()
PE1 = V((0, 0, 1)).cross(PA).normalized(); PE2 = PA.cross(PE1).normalized()
CPA = V((-0.114, 0.030, 0.738))
def pauld_dir(x, y):
    ax = math.radians(68) * x; ay = math.radians(-52 + 112 * (y + 1) / 2)
    return (PA + PE1 * math.tan(ax) + PE2 * math.tan(ay)).normalized()
def pauld_fn(x, y):
    d = pauld_dir(x, y)
    loc, n, i, dist = SBVH.ray_cast(CPA, d, 0.15)
    return CPA, d, (dist if loc is not None else float('nan'))
def keep_lateral(p):
    dc = d_cut(p)
    return p + NCUT * (0.0025 - dc) if dc < 0.0025 else p
PAULD, PO, PRR = build_plate("Robo_Plate_Pauldron", pauld_fn, (0.10, 0.10), LAY[2] + 0.0006, dome=0.0040, roll=0.0012, sm=45, trim_rows=2, post=keep_lateral, thick=0.0026)
PL.append(PAULD)
# shoulder emitter position (outer face of the pauldron, a little below the centre)
d_em = pauld_dir(0.0, -0.30)
loc, n, i, dist = SBVH.ray_cast(CPA, d_em, 0.15)
EMIT_P = CPA + d_em * (dist + LAY[2] + 0.0006 + 0.0035 * 0.95); EMIT_N = d_em
log("pauldron done")

PL += [
    arm_plate("Robo_Plate_Shoulder2", 0, 0.022, 0.080, -125, 128, 1, dome=0.0010, sm=6),
    arm_plate("Robo_Plate_UpperBack", 0, 0.070, 0.128, -132, -5, 0),
    arm_plate("Robo_Plate_UpperLat", 0, 0.070, 0.131, 2, 71, 0),
    arm_plate("Robo_Plate_UpperFront", 0, 0.074, 0.127, 81, 150, 0),
    arm_plate("Robo_Plate_UpperLow", 0, 0.104, 0.136, -40, 64, 1, dome=0.0008),
    arm_plate("Robo_Plate_ElbowCap", 1, -0.014, 0.020, -158, -38, 1, dome=0.0016, sm=6),
    arm_plate("Robo_Plate_ForeBackUp", 1, 0.016, 0.074, -138, -4, 0),
    arm_plate("Robo_Plate_ForeBackLow", 1, 0.064, 0.124, -142, -4, 1),
    arm_plate("Robo_Plate_ForeLat", 1, 0.020, 0.122, 2, 73, 0),
    arm_plate("Robo_Plate_ForeLatUp", 1, 0.020, 0.052, -30, 70, 1, dome=0.0008),
    arm_plate("Robo_Plate_ForeFront", 1, 0.024, 0.120, 83, 150, 0),
]
log("plates done", len(PL))

# ------------------------------------------------------------------ 3. glow channels + rings
def chan_line(th_deg, s0, s1, off, steps=90):
    pts = []
    for i in range(steps + 1):
        s = s0 + (s1 - s0) * i / steps
        k, t = (0, s) if s < L0 else (1, s - L0)
        A, d, r = radial(k, t, math.radians(th_deg))
        if not math.isnan(r): pts.append(A + d * (r + off))
    return smooth_pts(pts, 6)

GLOW = []
GLOW.append(tube_obj("Robo_Glow_FrontChannel", chan_line(76.5, 0.072, L0 + 0.123, 0.0021), 0.00085, M_BLUE))
GLOW.append(tube_obj("Robo_Glow_LatChannel", chan_line(-1.5, 0.072, L0 - 0.004, 0.0021), 0.0007, M_BLUE))
GLOW.append(tube_obj("Robo_Glow_LatChannelFore", chan_line(-1.0, L0 + 0.056, L0 + 0.123, 0.0021), 0.0007, M_BLUE))

def core_loop(pt, n, near, maxr=0.05):
    bm = bmesh.new(); bm.from_mesh(CORE.data)
    r = bmesh.ops.bisect_plane(bm, geom=list(bm.faces) + list(bm.edges) + list(bm.verts), dist=1e-7, plane_co=pt, plane_no=n)
    cut = [e for e in r['geom_cut'] if isinstance(e, bmesh.types.BMEdge) and (e.verts[0].co - near).length < maxr]
    adj = {}
    for e in cut:
        a, b = e.verts; adj.setdefault(a, []).append(b); adj.setdefault(b, []).append(a)
    best = []; seen = set()
    for v0 in adj:
        if v0 in seen: continue
        loop = [v0]; seen.add(v0); prev = None; cur = v0
        while True:
            nx = [w for w in adj[cur] if w is not prev and w not in seen]
            if not nx: break
            prev, cur = cur, nx[0]; seen.add(cur); loop.append(cur)
        if len(loop) > len(best): best = loop
    pts = [v.co.copy() for v in best]; bm.free(); return pts

def ring_pts(pt, n, near, lift):
    pts = core_loop(pt, n, near)
    if len(pts) < 8: return None
    c = sum(pts, V()) / len(pts)
    pts = smooth_pts(pts, 4, closed=True)
    return [p + (p - c).normalized() * lift for p in pts][::2]

def ring(name, pt, n, near, lift, rad, m):
    p = ring_pts(pt, n, near, lift)
    if p is None: log("ring failed", name); return None
    return tube_obj(name, p, rad, m, closed=True)

# elbow: ribbed bellows (gunmetal), blue rings above and below
for k in range(-4, 5):
    nn = (nEl + (u2 - u1) * (k * 0.06)).normalized()
    ring("Robo_ElbowRib_%d" % (k + 4), E + nEl * (k * 0.0032), nn, E, 0.0013, 0.00125, M_GUN)
ring("Robo_Glow_ElbowRingLow", E + u2 * 0.0175, u2, E + u2 * 0.0175, 0.0026, 0.0009, M_BLUE)
ring("Robo_Glow_ElbowRingUp", E - u1 * 0.0170, u1, E - u1 * 0.017, 0.0026, 0.0008, M_BLUE)
# wrist: blue ring, gold ring, ribs
ring("Robo_Glow_WristRing", E + u2 * 0.1265, u2, W, 0.0026, 0.0011, M_BLUE)
ring("Robo_WristGold", E + u2 * 0.1295, u2, W, 0.0024, 0.0008, M_GOLD)
for k in range(3):
    ring("Robo_WristRib_%d" % k, E + u2 * (0.1320 + k * 0.0026), u2, W, 0.0014, 0.0011, M_GUN)
# shoulder collar (covers the seam between the core and the marble torso) + gunmetal ring
def collar_pts(lift, lat):
    out = []
    for p in CL:
        r = (p - CLC).normalized()
        out.append(p + r * (lift - 0.0012) + NCUT * lat)
    return out[::2]
tube_obj("Robo_Collar_Gold", collar_pts(0.0012, 0.0004), 0.0026, M_GOLD, closed=True)
tube_obj("Robo_Collar_Gun", collar_pts(0.0010, 0.0050), 0.0018, M_GUN, closed=True)
log("rings done")

# ------------------------------------------------------------------ 4. mechanics (inner side)
MECH = Acc("Robo_Mechanics", [M_GUN, M_STEEL, M_GOLD, M_BLUE, M_DARK])
def piston(k, t0, t1, th, lift=0.0006, rb=0.0021):
    A0, d0, r0 = radial(k, t0, math.radians(th)); A1, d1, r1 = radial(k, t1, math.radians(th))
    p0 = A0 + d0 * (r0 + lift); p1 = A1 + d1 * (r1 + lift)
    ax = (p1 - p0); L = ax.length; ax.normalize()
    lb = L * 0.58
    MECH.add_bm(bm_cyl(rb, lb, 20, bev=0.0004), frame(p0 + ax * (lb / 2), ax), 0)
    MECH.add_bm(bm_cyl(rb * 0.48, L - lb + 0.002, 14), frame(p0 + ax * (lb + (L - lb) / 2 - 0.001), ax), 1)
    for p, r in ((p0, rb * 1.15), (p1, rb * 0.9)):
        MECH.add_bm(bm_sphere(r, 14, 8), Matrix.Translation(p), 0)
    MECH.add_bm(bm_cyl(rb * 1.12, 0.0012, 20), frame(p0 + ax * (lb - 0.0006), ax), 2)
    MECH.add_bm(bm_cyl(rb * 1.12, 0.0010, 20), frame(p0 + ax * 0.004, ax), 2)

piston(0, 0.050, 0.128, 182); piston(0, 0.060, 0.120, 208, rb=0.0017)
piston(1, 0.028, 0.116, 178); piston(1, 0.036, 0.110, 204, rb=0.0017)
piston(0, 0.040, 0.100, 158, rb=0.0015); piston(1, 0.030, 0.090, 228, rb=0.0015)
# cables along the inner side, shoulder to wrist
CAB = []
for i, (th, ph) in enumerate(((166, 0.0), (194, 1.3), (217, 2.4), (232, 0.7))):
    pts = []
    for j in range(121):
        s = 0.036 + (L0 + 0.126 - 0.036) * j / 120
        k, t = (0, s) if s < L0 else (1, s - L0)
        A, d, r = radial(k, t, math.radians(th + 5 * math.sin(s * 70 + ph)))
        if not math.isnan(r): pts.append(A + d * (r + 0.0003 + 0.0012 * (0.5 + 0.5 * math.sin(s * 45 + ph))))
    CAB.append(tube_obj("Robo_Cable_%d" % i, smooth_pts(pts, 5), 0.00075, M_DARK if i % 2 else M_GUN))
    # clamps
    for j in range(8, len(pts) - 4, 22):
        p = pts[j]; ax = (pts[j + 1] - pts[j - 1]).normalized()
        MECH.add_bm(bm_cyl(0.0011, 0.0018, 12), frame(p, ax), 2)
# elbow hinge discs (lateral + medial)
hinge = u1.cross(u2).normalized()
if hinge.x > 0: hinge = -hinge
for side in (hinge, -hinge):
    loc, nor, i, dd = CBVH.ray_cast(E + side * 0.06, -side, 0.1)
    if loc is None: continue
    p = loc + nor * 0.0012
    MECH.add_bm(bm_cyl(0.0062, 0.0030, 32, bev=0.0006), frame(p, nor), 0)
    MECH.add_bm(bm_torus(0.0060, 0.0008, 40, 8), frame(p + nor * 0.0015, nor), 2)
    MECH.add_bm(bm_cyl(0.0030, 0.0012, 24), frame(p + nor * 0.0016, nor), 3)
# shoulder socket dots between the collar rings
cp = collar_pts(0.0022, 0.0085)
for kk in range(0, len(cp), max(1, len(cp) // 16)):
    MECH.add_bm(bm_sphere(0.0012, 12, 8), Matrix.Translation(cp[kk]), 3)
# shoulder emitter: gold rim, dark bezel, bright disc
MECH.add_bm(bm_cyl(0.0125, 0.0024, 48, bev=0.0006), frame(EMIT_P, EMIT_N), 2)
MECH.add_bm(bm_cyl(0.0102, 0.0010, 48), frame(EMIT_P + EMIT_N * 0.0012, EMIT_N), 0)
MECH.add_bm(bm_torus(0.0080, 0.0007, 48, 8), frame(EMIT_P + EMIT_N * 0.0018, EMIT_N), 3)
MECH.add_bm(bm_torus(0.0102, 0.0006, 48, 8), frame(EMIT_P + EMIT_N * 0.0017, EMIT_N), 2)
EMITTER = Acc("Robo_ShoulderEmitter_Glow", [M_BLUE_HOT])
EMITTER.add_bm(bm_cyl(0.0060, 0.0014, 40, bev=0.0004), frame(EMIT_P + EMIT_N * 0.0016, EMIT_N), 0)
log("mechanics done")

# ------------------------------------------------------------------ 5. hand
HAND = Acc("Robo_Hand", [M_IVORY, M_GUN, M_GOLD, M_BLUE, M_STEEL])
X = V((1, 0, 0)); Y = V((0, 1, 0)); Z = V((0, 0, 1))
# wrist bearing
wc = W + u3 * 0.0035
HAND.add_bm(bm_cyl(1.0, 0.009, 32, bev=0.0), frame(wc, u3, Y) @ Matrix.Diagonal((0.0115, 0.0165, 1, 1)), 1)
for k in range(2):
    HAND.add_bm(bm_torus(1.0, 0.07, 40, 8), frame(wc + u3 * (-0.003 + k * 0.003), u3, Y) @ Matrix.Diagonal((0.0118, 0.0168, 0.012, 1)), 1)
HAND.add_bm(bm_torus(1.0, 0.06, 40, 8), frame(wc + u3 * 0.0048, u3, Y) @ Matrix.Diagonal((0.0122, 0.0172, 0.012, 1)), 2)
# palm core (gunmetal) + dorsal ivory plate with gold rim + knuckle bar
PC = V((-0.1700, -0.0045, 0.4745))
HAND.add_bm(bm_cube(0.0165, 0.0405, 0.044, bev=0.0045), Matrix.Translation(PC), 1)
def palm_plate(cz, hz, hy, lift, mi_body=0, name=None):
    nu, nv = 28, 30; bm = bmesh.new(); vg = {}
    for i in range(nu + 1):
        for j in range(nv + 1):
            x = -1 + 2 * i / nu; y = -1 + 2 * j / nv
            mx = max(abs(x), abs(y)); n4 = (x ** 4 + y ** 4) ** 0.25
            sx, sy = (x * mx / n4, y * mx / n4) if n4 > 0 else (0, 0)
            px = -0.1785 - lift - 0.0016 * (1 - mx * mx) + 0.0035 * sy * sy
            vg[i, j] = bm.verts.new((px, PC.y + sy * hy, cz + sx * hz))
    for i in range(nu):
        for j in range(nv):
            f = bm.faces.new((vg[i, j], vg[i, j + 1], vg[i + 1, j + 1], vg[i + 1, j]))
            f.material_index = 2 if (i == 0 or j == 0 or i == nu - 1 or j == nv - 1) else mi_body
    bm.normal_update()
    if sum(f.normal.x for f in bm.faces) > 0: bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
    sol = bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=0.0018)
    HAND.add_bm(bm, Matrix(), 0)
palm_plate(0.4795, 0.0170, 0.0190, 0.0)
palm_plate(0.4590, 0.0060, 0.0195, 0.0016)
for sg in (-1, 1):   # ivory side plates with gold edge
    c = PC + V((-0.0010, sg * 0.0207, 0.0030))
    HAND.add_bm(bm_cube(0.0132, 0.0024, 0.0330, bev=0.0010, segs=2), Matrix.Translation(c), 2)
    HAND.add_bm(bm_cube(0.0118, 0.0024, 0.0316, bev=0.0010, segs=2), Matrix.Translation(c + V((0, sg * 0.0006, 0))), 0)
for (dy, dz, sx, sy, sz) in ((-0.012, 0.010, 0.004, 0.014, 0.020), (0.008, 0.012, 0.0035, 0.016, 0.018), (-0.004, -0.012, 0.0035, 0.034, 0.008)):
    HAND.add_bm(bm_cube(sx, sy, sz, bev=0.0015, segs=3), Matrix.Translation(PC + V((0.0085, dy, dz))), 0)
# fingers
FING = [  # name, mcp (y, z), spread deg, lengths, flex (mcp, pip, dip), width
    ("Index", -0.0190, 0.4535, -5.0, (0.0190, 0.0125, 0.0100), (12, 30, 20), 0.0090),
    ("Middle", -0.0085, 0.4510, -1.5, (0.0210, 0.0135, 0.0105), (15, 34, 22), 0.0094),
    ("Ring", 0.0020, 0.4520, 2.5, (0.0200, 0.0128, 0.0100), (18, 38, 24), 0.0088),
    ("Pinky", 0.0118, 0.4555, 7.0, (0.0160, 0.0105, 0.0090), (22, 42, 26), 0.0078),
]
TIPS = {}
def rot(v, ax, deg): return (Matrix.Rotation(math.radians(deg), 3, ax) @ v).normalized()
def finger(name, base, s0, toward, lens, flex, w, thumb=False):
    ax = s0.cross(toward).normalized()
    s = s0.copy(); p = base.copy()
    dirs = []
    for i in range(3):
        s = rot(s, ax, flex[i]); dirs.append(s)
    joints = [p]
    for L, s in zip(lens, dirs):
        p = p + s * L; joints.append(p)
    for i in range(3):
        a, b, s = joints[i], joints[i + 1], dirs[i]
        dors = s.cross(ax).normalized()
        L = (b - a).length
        # joint (gunmetal axle across the finger) + gold washers + glowing knuckle dot
        jr = w * (0.42 if i == 0 else 0.38)
        HAND.add_bm(bm_cyl(jr, w * 1.02, 20, bev=0.0004), frame(a, ax, s), 1)
        for sg in (-1, 1):
            HAND.add_bm(bm_cyl(jr * 0.75, 0.0006, 16), frame(a + ax * sg * w * 0.53, ax, s), 2)
        HAND.add_bm(bm_sphere(0.0017 if i == 0 else 0.0015, 14, 8), Matrix.Translation(a + dors * (jr + 0.0004)), 3)
        # inner phalanx link (gunmetal)
        HAND.add_bm(bm_cube(w * 0.55, w * 0.5, L, bev=0.0008, segs=2), frame((a + b) / 2 - dors * w * 0.08, s, dors), 1)
        # ivory cover (dorsal shell), tapered by scaling
        cl = L - jr * 1.15 if i < 2 else L + 0.0012
        cw = w * (1.0 - 0.06 * i); ct = w * 0.62
        cc = a + s * (jr * 0.6 + cl / 2) + dors * (w * 0.14)
        HAND.add_bm(bm_cube(cw, ct, cl, bev=min(cw, ct) * 0.36, segs=3), frame(cc, s, dors) @ Matrix.Diagonal((1, 1, 1, 1)), 0)
        # gold edge strip at the proximal end of each cover
        HAND.add_bm(bm_cube(cw * 1.02, ct * 1.02, 0.0007, bev=min(cw, ct) * 0.34, segs=2), frame(a + s * (jr * 0.6 + 0.0006) + dors * (w * 0.14), s, dors), 2)
    TIPS[name] = joints[-1]
    return joints

for nm, y, z, spr, lens, flex, w in FING:
    s0 = rot(V((0, 0, -1)), X, spr)
    finger(nm, V((-0.1725, y, z)), s0, X, lens, flex, w)
# thumb: from the front edge of the palm, down/forward, slight curl toward the palm
tb = V((-0.1655, -0.0245, 0.4895))
HAND.add_bm(bm_sphere(0.0052, 18, 10), Matrix.Translation(tb), 1)
finger("Thumb", tb, V((0.16, -0.36, -0.92)).normalized(), V((0.7, 0.5, 0)).normalized(), (0.0175, 0.0145, 0.0115), (6, 14, 14), 0.0092, True)
log("hand done; tips", {k: tuple(round(c, 3) for c in v) for k, v in TIPS.items()})

for acc in (MECH, EMITTER, HAND):
    acc.build(40)

# ------------------------------------------------------------------ 6. headband
log("headband")
co = np.empty(len(SCULPT.data.vertices) * 3); SCULPT.data.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
HC = V((-0.031, -0.002, 0.0)); FACE = V((0.81, -0.59, 0)).normalized()
def zband(th):
    d = V((math.cos(th), math.sin(th), 0)); return 0.9480 + 0.0035 * d.dot(FACE)
head = co[(co[:, 2] > 0.90) & (co[:, 2] < 0.99) & (np.hypot(co[:, 0] - HC.x, co[:, 1] - HC.y) < 0.11)]
ang = np.arctan2(head[:, 1] - HC.y, head[:, 0] - HC.x); rad = np.hypot(head[:, 0] - HC.x, head[:, 1] - HC.y)
NB = 240; BH = 0.0105
def envelope(zoff, win=0.0018, pct=92):
    rm = np.zeros(NB)
    for i in range(NB):
        th = -math.pi + (i + 0.5) * 2 * math.pi / NB; zc = zband(th) + zoff
        dth = np.angle(np.exp(1j * (ang - th)))
        mk = (np.abs(dth) < 2 * math.pi / NB * 1.5) & (np.abs(head[:, 2] - zc) < win)
        rm[i] = np.percentile(rad[mk], pct) if mk.sum() > 5 else 0
    for i in range(NB):
        if rm[i] == 0: rm[i] = max(rm[i - 1], rm[(i + 1) % NB])
    e = rm.copy()
    for _ in range(30):
        e = np.maximum(e, rm - 0.0005); e = (np.roll(e, 1) + 2 * e + np.roll(e, -1)) / 4
    return np.maximum(e, rm - 0.0006)
EB = envelope(-BH / 2); ET = envelope(BH / 2); EM = envelope(0.0)
RIN = np.maximum(np.maximum(EB, ET), EM) + 0.0004
for _ in range(10): RIN = np.maximum(RIN, (np.roll(RIN, 1) + 2 * RIN + np.roll(RIN, -1)) / 4)
log("head radius", RIN.min(), RIN.max())
BT = 0.0030
def band_ring(name, r0, thick, h, zoff, m, bev=0.0005):
    bmb = bmesh.new(); rings = []
    for i in range(NB):
        th = -math.pi + (i + 0.5) * 2 * math.pi / NB; d = V((math.cos(th), math.sin(th), 0))
        r = RIN[i] + r0; zc = zband(th) + zoff
        prof = [(r, -h / 2), (r + thick, -h / 2), (r + thick, h / 2), (r, h / 2)]
        rings.append([bmb.verts.new(HC + d * pr + V((0, 0, zc + pz))) for pr, pz in prof])
    for i in range(NB):
        a, b = rings[i], rings[(i + 1) % NB]
        for k in range(4): bmb.faces.new((a[k], b[k], b[(k + 1) % 4], a[(k + 1) % 4]))
    bmb.normal_update(); bmesh.ops.recalc_face_normals(bmb, faces=bmb.faces)
    me = D.meshes.new(name); bmb.to_mesh(me); bmb.free(); me.materials.append(m); finish_mesh(me, 50)
    ob = link(D.objects.new(name, me))
    mm = ob.modifiers.new("bev", 'BEVEL'); mm.width = bev; mm.segments = 2; mm.limit_method = 'ANGLE'
    return ob
band_ring("Neuro_Band", 0.0, BT, BH, 0.0, M_NGOLD)
band_ring("Neuro_Band_LipTop", BT - 0.0002, 0.0010, 0.0011, BH / 2 - 0.00075, M_NGOLD, 0.0003)
band_ring("Neuro_Band_LipBot", BT - 0.0002, 0.0010, 0.0011, -BH / 2 + 0.00075, M_NGOLD, 0.0003)
band_ring("Neuro_Band_Glow", BT - 0.0003, 0.0012, 0.0056, 0.0, M_AMBER, 0.0003)
def band_point(th, extra):
    i = ((th + math.pi) / (2 * math.pi) * NB - 0.5) % NB
    r = float(np.interp(i, np.arange(NB), RIN, period=NB)); d = V((math.cos(th), math.sin(th), 0))
    return HC + d * (r + extra) + V((0, 0, zband(th))), d
fa = math.atan2(FACE.y, FACE.x)
NEURO = Acc("Neuro_Modules", [M_NGOLD, M_GUN, M_LENS])
NGLOW = Acc("Neuro_Modules_Glow", [M_RING])
for nm, off, rr in (("Front", 0.0, 0.0112), ("TempleL", math.radians(80), 0.0095),
                    ("TempleR", math.radians(-80), 0.0095), ("Back", math.pi, 0.0100)):
    p, d = band_point(fa + off, BT + 0.0016)
    tang = Z.cross(d).normalized()
    NEURO.add_bm(bm_cyl(rr, 0.0050, 56, bev=0.0012), frame(p, d), 0)
    NEURO.add_bm(bm_cyl(rr * 0.80, 0.0012, 56), frame(p + d * 0.0026, d), 1)
    NEURO.add_bm(bm_torus(rr * 0.92, rr * 0.07, 56, 8), frame(p + d * 0.0026, d), 0)
    NGLOW.add_bm(bm_torus(rr * 0.64, rr * 0.12, 56, 10), frame(p + d * 0.0032, d), 0)
    lens = bm_sphere(rr * 0.42, 32, 16)
    NEURO.add_bm(lens, frame(p + d * 0.0030, d) @ Matrix.Diagonal((1, 1, 0.45, 1)), 2)
    # side clamps where the module meets the band
    for sg in (-1, 1):
        NEURO.add_bm(bm_cube(0.0032, 0.0042, BH * 1.08, bev=0.0006, segs=2),
                     frame(p + tang * sg * (rr + 0.0010) - d * 0.0010, Z, d), 1)
NEURO.build(35); NGLOW.build(35)
log("headband done")

# ------------------------------------------------------------------ cleanup / save
for o in (ARMREF, SMOOTH):
    me = o.data; D.objects.remove(o, do_unlink=True); D.meshes.remove(me)
SCULPT["cyber"] = 2
for coll in (D.meshes, D.curves, D.materials):
    for m in list(coll):
        if m.users == 0: coll.remove(m)
log("objects in Cyber", len(COL.objects) if COL else None)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
log("saved", OUT)
