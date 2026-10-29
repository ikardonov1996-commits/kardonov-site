# Cyber David v6 (round-6: new robotic hand fitted to the marble right hand, AI_Titanium v2 + lighter joints,
# grey reflection-only world, calmer neon (planar collar, straight channels ending on plate-end rings), softer headband glow).
# Run:  blender -b assets/asset_statue_cyber_v1.blend -P build6.py -- out/cyber/stage_cut.blend OUT.blend
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
M_BLUE = mat("Cyber_GlowBlue", (0.05, 0.40, 1.0), rough=0.3, emis=(0.02, 0.30, 1.0), estr=4.0, vp=(0.25, 0.66, 1.0))
M_BLUE_HOT = mat("Cyber_GlowBlueHot", (0.2, 0.6, 1.0), rough=0.3, emis=(0.03, 0.34, 1.0), estr=6.0, vp=(0.5, 0.8, 1.0))
M_NGOLD = mat("Neuro_Gold", (1.0, 0.58, 0.20), metal=1.0, rough=0.28)
M_AMBER = mat("Neuro_GlowAmber", (0.05, 0.015, 0.0), rough=0.3, emis=(1.0, 0.36, 0.04), estr=0.9, vp=(1.0, 0.6, 0.2))
M_RING = mat("Neuro_GlowRing", (0.05, 0.015, 0.0), rough=0.3, emis=(1.0, 0.36, 0.04), estr=1.7, vp=(1.0, 0.5, 0.1))
import os
# v5: ONE shared light cool-grey AI metal (shared with chisel + windlass handle; parameters untouched)
sys.path.insert(0, "/tmp/claude-0/-home-user-kardonov-site/cb30cd45-1b88-5b9b-b3ff-480343f6cfce/scratchpad/scripts")
from mat_ai_titanium import ai_titanium
M_NGUN = M_GUN                       # headband bezels keep the v4 dark gunmetal (headband unchanged)
M_IVORY = ai_titanium()              # all plates, hand shells, finger covers
# joints / mechanics in the gaps: same family, a step darker so the plates read as separate parts
M_JOINT = mat("AI_Titanium_Joint", (0.40, 0.42, 0.455), metal=0.85, rough=0.42)   # v6: lighter mid-grey, same family
M_GUN = M_JOINT
M_GOLD = M_JOINT                     # arm trim slot (plate rims, hinge, emitter bezel) -> darker titanium, NOT neon
M_DARK = mat("AI_Rubber", (0.11, 0.115, 0.13), rough=0.55)   # cables / finger axles: dark grey, not black
PLATE_TRIM = 0
NRAD = 0.00075                       # ONE neon line thickness for the whole arm (tube radius, m)
AI_TOOLS = True
print("AI materials:", M_IVORY.name, M_JOINT.name, flush=True)
M_LENS = mat("Neuro_Lens", (0.30, 0.10, 0.02), metal=0.3, rough=0.12, emis=(1.0, 0.38, 0.05), estr=0.8)

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

SMOOTH = layer_copy("tmp_smooth", 6, 0.5, 0.0)
SBVH = BVHTree.FromObject(SMOOTH, bpy.context.evaluated_depsgraph_get())

WJ0 = 0.1240   # forearm plates / core end (start of the wrist joint)
# core (gunmetal body visible in gaps): 2 mm inside the marble, open at shoulder cut, cut at the wrist
CORE = layer_copy("Robo_Core", 5, 0.4, -0.0022)
bm = bmesh.new(); bm.from_mesh(CORE.data)
bmesh.ops.bisect_plane(bm, geom=list(bm.faces) + list(bm.edges) + list(bm.verts), dist=1e-7, plane_co=P0 + NCUT * 0.0010, plane_no=NCUT, clear_inner=True)
kill = [f for f in bm.faces if sd(f.calc_center_median(), E + u2 * WJ0, u2) > 0]
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
RC = np.where(np.isnan(RC), np.nanmedian(RC), RC); RM = np.where(np.isnan(RM), RC + 0.0022, RM)
RM = np.minimum(RM, RC + 0.0035)
for _ in range(10): RM = (np.roll(RM, 1) + 2 * RM + np.roll(RM, -1)) / 4
CL = [C0 + NCUT * 0.0004 + (ce1 * math.cos(2 * math.pi * i / NA) + ce2 * math.sin(2 * math.pi * i / NA)) * (RM[i] - 0.0005) for i in range(NA)]
CLC = C0
# v6: the collar used to follow the marble cut outline exactly (S-wiggles at the armpit). Now: the marble outline is
# low-passed with Fourier descriptors over arc length (|k| <= 5) and set 2 mm inside -> one calm planar curve on the socket.
_ang = np.array([2 * math.pi * i / NA for i in range(NA)])
_P = np.stack([RM * np.cos(_ang), RM * np.sin(_ang)], 1)
_seg = np.linalg.norm(np.diff(np.vstack([_P, _P[:1]]), axis=0), axis=1); _s = np.concatenate([[0], np.cumsum(_seg)])
_n = 256; _u = np.linspace(0, _s[-1], _n, endpoint=False)
_z = np.interp(_u, _s, np.append(_P[:, 0], _P[0, 0])) + 1j * np.interp(_u, _s, np.append(_P[:, 1], _P[0, 1]))
_F = np.fft.fft(_z); _F[np.abs(np.fft.fftfreq(_n, 1 / _n)) > 5] = 0; _z = np.fft.ifft(_F)
_Q = np.stack([_z.real, _z.imag], 1); _T = np.roll(_Q, -1, 0) - np.roll(_Q, 1, 0)
_N = np.stack([_T[:, 1], -_T[:, 0]], 1); _N /= np.linalg.norm(_N, axis=1)[:, None]
if np.mean(np.sum((_Q - _Q.mean(0)) * _N, 1)) > 0: _N = -_N          # inward normals
_Q = _Q + _N * 0.0020
_dm = np.min(np.linalg.norm(_Q[:, None] - _P[None], axis=2), 1)
print("collar: Fourier |k|<=5, dist to marble outline min %.4f max %.4f" % (_dm.min(), _dm.max()), flush=True)
CLN = [C0 + NCUT * 0.0004 + ce1 * q[0] + ce2 * q[1] for q in _Q]
# recess the core near the cut: socket sits inside the gap, nothing proud of the chest
REC_D, REC_A = 0.032, 0.0065
for v in CORE.data.vertices:
    dc = d_cut(v.co)
    if dc < REC_D:
        q = min(max(1.0 - dc / REC_D, 0.0), 1.0); q = q * q * (3 - 2 * q)
        ax_ = C0 + NCUT * dc; r_ = v.co - ax_; L_ = r_.length
        if L_ > 1e-6: v.co = ax_ + r_ * ((L_ - REC_A * q) / L_)
CORE.data.update()
CB0 = BVHTree.FromObject(CORE, bpy.context.evaluated_depsgraph_get())
sock = bmesh.new(); ring_v = [sock.verts.new(C0 + NCUT * 0.0003 + (p - C0 - NCUT * 0.0004) * 1.0) for p in CL[::2]]
cen = sock.verts.new(C0 + NCUT * 0.0003)
for i in range(len(ring_v)): sock.faces.new((cen, ring_v[i], ring_v[(i + 1) % len(ring_v)]))
me_s = D.meshes.new("Robo_Socket"); sock.to_mesh(me_s); sock.free(); me_s.materials.append(M_DARK); finish_mesh(me_s, 80)
link(D.objects.new("Robo_Socket", me_s))
CDOTS = []
for i in range(0, NA, 12):
    a_ = 2 * math.pi * i / NA; dv = ce1 * math.cos(a_) + ce2 * math.sin(a_)
    loc, n_, k_, dd = CB0.ray_cast(C0 + NCUT * 0.0045, dv, 0.08)
    if loc is not None: CDOTS.append(loc + n_ * 0.0006)
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
LAY = [0.0026, 0.0047, 0.0068]; THK = 0.0022
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

def build_plate(name, ray_fn, sizes, off, dome=0.0012, roll=0.0007, sm=4, trim_rows=None, thick=THK, post=None):
    if trim_rows is None: trim_rows = PLATE_TRIM
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

def arm_plate(name, k, t0, t1, th0, th1, layer, skew=0.0, **kw):
    th0, th1 = math.radians(th0), math.radians(th1)
    a, u, lat, fr, L = seg(k)
    off = LAY[layer]
    def fn(x, y):
        t = t0 + (t1 - t0) * (x + 1) / 2 + skew * y; th = th0 + (th1 - th0) * (y + 1) / 2
        A, d, r = radial(k, t, th)
        if k == 1:      # anatomical taper: plates hug the forearm tighter toward the wrist
            q = min(max((t / L - 0.45) / 0.55, 0.0), 1.0); q = q * q * (3 - 2 * q)
            r -= off * 0.45 * q
        return A, d, r
    rmean = 0.024
    return build_plate(name, fn, (t1 - t0, rmean * (th1 - th0)), LAY[layer], **kw)[0]

PL = []
# pauldron: spherical cap around the shoulder joint
PA = V((-1, 0.04, 0.62)).normalized()
PE1 = V((0, 0, 1)).cross(PA).normalized(); PE2 = PA.cross(PE1).normalized()
CPA = V((-0.114, 0.030, 0.738))
def pauld_dir(x, y):
    ax = math.radians(68) * x; ay = math.radians(-52 + 121 * (y + 1) / 2)
    return (PA + PE1 * math.tan(ax) + PE2 * math.tan(ay)).normalized()
def pauld_fn(x, y):
    d = pauld_dir(x, y)
    loc, n, i, dist = SBVH.ray_cast(CPA, d, 0.15)
    dn = d.dot(NCUT); tp = (P0 + NCUT * 0.0025 - CPA).dot(NCUT) / dn if dn < -1e-6 else 1e9   # ray meets the cut plane
    if loc is None: dist = tp
    dist = min(dist, tp)
    return CPA, d, (dist if dist < 1e8 else float('nan'))
def keep_lateral(p):
    dc = d_cut(p)
    return p + NCUT * (0.0025 - dc) if dc < 0.0025 else p
_g = np.array([[pauld_fn(x, y)[2] for y in np.linspace(-1, 1, 9)] for x in np.linspace(-1, 1, 9)])
log("pauldron ray dist grid (rows x, cols y)\n" + np.array2string(_g * 1000, precision=0, max_line_width=200))
PAULD, PO, PRR = build_plate("Robo_Plate_Pauldron", pauld_fn, (0.10, 0.10), LAY[2] + 0.0006, dome=0.0040, roll=0.0012, sm=45, post=keep_lateral, thick=0.0026)
PL.append(PAULD)
# shoulder emitter position (outer face of the pauldron, a little below the centre)
d_em = pauld_dir(0.0, -0.30)
loc, n, i, dist = SBVH.ray_cast(CPA, d_em, 0.15)
EMIT_P = CPA + d_em * (dist + LAY[2] + 0.0006 + 0.0035 * 0.95); EMIT_N = d_em
log("pauldron done")

PL += [
    arm_plate("Robo_Plate_Shoulder2", 0, 0.024, 0.078, -125, 128, 1, skew=0.008, dome=0.0010, sm=3),
    arm_plate("Robo_Plate_UpperBack", 0, 0.070, 0.128, -132, -5, 0, sm=2),
    arm_plate("Robo_Plate_UpperLat", 0, 0.070, 0.131, 2, 71, 0, sm=2),
    arm_plate("Robo_Plate_UpperFront", 0, 0.074, 0.127, 81, 150, 0, sm=2, dome=0.0016),
    arm_plate("Robo_Plate_UpperLow", 0, 0.106, 0.134, -40, 64, 1, skew=0.008, dome=0.0008, sm=2),
    arm_plate("Robo_Plate_ElbowCap", 1, -0.014, 0.020, -158, -38, 1, dome=0.0016, sm=4),
    arm_plate("Robo_Plate_ForeBackUp", 1, 0.016, 0.074, -138, -4, 0, sm=2, dome=0.0016),
    arm_plate("Robo_Plate_ForeBackLow", 1, 0.064, 0.112, -142, -4, 1, skew=-0.010, sm=2),
    arm_plate("Robo_Plate_ForeLat", 1, 0.020, 0.1215, 2, 73, 0, sm=2),
    arm_plate("Robo_Plate_ForeLatUp", 1, 0.020, 0.054, -30, 70, 1, skew=0.008, dome=0.0008, sm=2),
    arm_plate("Robo_Plate_ForeFront", 1, 0.024, 0.1205, 83, 150, 0, sm=2),
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
CAPS = []        # v5: no end caps / dots - every line ends in a ring or under a plate edge

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

# v6 neon layout on the arm: every channel runs straight in its plate seam (constant radius) and ends perpendicular on a
# closed ring that hugs the END of the plating (upper arm -> elbow ring, forearm -> wrist ring). No ribs, no dips/S-bends.
NOFF = 0.0016                     # neon centre height above the smoothed marble (mid-thickness of the seam/plate ends)
def off_at(k, t, off):            # forearm plates taper toward the wrist: neon follows the same taper
    if k != 1: return off
    q = min(max((t / L1 - 0.45) / 0.55, 0.0), 1.0); q = q * q * (3 - 2 * q)
    return off - LAY[0] * 0.45 * q
def end_ring(k, t, off, n=160):
    rr = np.array([radial(k, t, 2 * math.pi * i / n)[2] for i in range(n)]); rr = fill_nan(rr)
    for _ in range(4): rr = (np.roll(rr, 1) + 2 * rr + np.roll(rr, -1)) / 4
    a, u, lat, fr, L = seg(k); A = a + u * t; o = off_at(k, t, off)
    return [A + (lat * math.cos(2 * math.pi * i / n) + fr * math.sin(2 * math.pi * i / n)) * (rr[i] + o) for i in range(n)], rr
def straight_channel(name, k, th, t0, t1, ringp, off=NOFF, steps=160):
    pts = []
    for i in range(steps + 1):
        t = t0 + (t1 - t0) * i / steps; A, d, r = radial(k, t, math.radians(th))
        if not math.isnan(r): pts.append(A + d * (r + off_at(k, t, off)))
    pts = smooth_pts(pts, 6)
    tgt = min(ringp, key=lambda q: (q - pts[-1]).length); gap = (tgt - pts[-1]).length
    n_ = 8
    for i in range(1, n_ + 1): pts[-i] = pts[-i] + (tgt - pts[-1]) * ((n_ - i + 1) / n_)   # < 1 mm snap, linear fade
    ob = tube_obj(name, pts, NRAD, M_BLUE)
    log(name, "snap %.5f m" % gap, "len %.3f" % sum((pts[i + 1] - pts[i]).length for i in range(len(pts) - 1)))
    return ob
T_UP_END = 0.1305                 # upper-arm plating ends (UpperLat 0.131 / UpperFront 0.127 / UpperBack 0.128)
T_FO_END = 0.1220                 # forearm plating ends (ForeLat 0.1215 / ForeFront 0.1205)
ELB_PTS, _ = end_ring(0, T_UP_END, NOFF)
tube_obj("Robo_Glow_ElbowRing", ELB_PTS[::2], NRAD, M_BLUE, closed=True)
WR_PTS, _ = end_ring(1, T_FO_END, NOFF)
tube_obj("Robo_Glow_WristRing", WR_PTS[::2], NRAD, M_BLUE, closed=True)
WR_C = E + u2 * T_FO_END
tube_obj("Robo_Glow_Collar", CLN[::2], NRAD, M_BLUE, closed=True)
# upper arm: seam UpperLat | UpperFront, from under the Shoulder2 plate (fold) straight down onto the elbow ring
GLOW.append(straight_channel("Robo_Glow_ChannelUpper", 0, 76.5, 0.064, T_UP_END, ELB_PTS))
# forearm: seam ForeLat | ForeBack, from under the ForeLatUp plate (fold) straight down onto the wrist ring
GLOW.append(straight_channel("Robo_Glow_ChannelFore", 1, -1.0, 0.046, T_FO_END, WR_PTS))
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
    MECH.add_bm(bm_cyl(rb * 1.12, 0.0012, 20), frame(p0 + ax * (lb - 0.0006), ax), 1 if AI_TOOLS else 2)
    MECH.add_bm(bm_cyl(rb * 1.12, 0.0010, 20), frame(p0 + ax * 0.004, ax), 1 if AI_TOOLS else 2)

piston(0, 0.050, 0.128, 182); piston(0, 0.060, 0.120, 208, rb=0.0017)
piston(1, 0.028, 0.116, 178); piston(1, 0.036, 0.110, 204, rb=0.0017)
piston(0, 0.040, 0.100, 158, rb=0.0015); piston(1, 0.030, 0.090, 228, rb=0.0015)
# cables along the inner side, shoulder to wrist
CAB = []
for i, (th, ph) in enumerate(((166, 0.0), (194, 1.3), (217, 2.4), (232, 0.7))):
    pts = []
    for j in range(121):
        s = 0.036 + (L0 + 0.110 - 0.036) * j / 120
        k, t = (0, s) if s < L0 else (1, s - L0)
        A, d, r = radial(k, t, math.radians(th + 5 * math.sin(s * 70 + ph)))
        if not math.isnan(r): pts.append(A + d * (r + 0.0003 + 0.0012 * (0.5 + 0.5 * math.sin(s * 45 + ph))))
    CAB.append(tube_obj("Robo_Cable_%d" % i, smooth_pts(pts, 5), 0.00075, M_DARK if i % 2 else M_GUN))
    # clamps
    for j in range(8, len(pts) - 4, 22):
        p = pts[j]; ax = (pts[j + 1] - pts[j - 1]).normalized()
        MECH.add_bm(bm_cyl(0.0011, 0.0018, 12), frame(p, ax), 1 if AI_TOOLS else 2)
# elbow hinge discs (lateral + medial)
hinge = u1.cross(u2).normalized()
if hinge.x > 0: hinge = -hinge
for side in (hinge, -hinge):
    loc, nor, i, dd = CBVH.ray_cast(E + side * 0.06, -side, 0.1)
    if loc is None: continue
    p = loc + nor * 0.0012
    MECH.add_bm(bm_cyl(0.0062, 0.0030, 32, bev=0.0006), frame(p, nor), 0)
    MECH.add_bm(bm_torus(0.0060, 0.0008, 40, 8), frame(p + nor * 0.0015, nor), 2)
    MECH.add_bm(bm_cyl(0.0030, 0.0012, 24), frame(p + nor * 0.0016, nor), 1)   # v5: steel hub, no neon (ring would cross the elbow ring)
for p_, r_ in CAPS:
    MECH.add_bm(bm_sphere(r_, 14, 10), Matrix.Translation(p_), 3)
# shoulder socket dots between the collar rings
# v5: socket dots removed
# shoulder emitter: gold rim, dark bezel, bright disc
MECH.add_bm(bm_cyl(0.0125, 0.0024, 48, bev=0.0006), frame(EMIT_P, EMIT_N), 2)
MECH.add_bm(bm_cyl(0.0102, 0.0010, 48), frame(EMIT_P + EMIT_N * 0.0012, EMIT_N), 0)
MECH.add_bm(bm_torus(0.0080, NRAD, 48, 8), frame(EMIT_P + EMIT_N * 0.0018, EMIT_N), 3)   # neon ring (closed)
MECH.add_bm(bm_torus(0.0102, 0.0006, 48, 8), frame(EMIT_P + EMIT_N * 0.0017, EMIT_N), 2)
EMITTER = Acc("Robo_ShoulderEmitter_Glow", [M_BLUE_HOT])
EMITTER.add_bm(bm_cyl(0.0060, 0.0014, 40, bev=0.0004), frame(EMIT_P + EMIT_N * 0.0016, EMIT_N), 0)
# shoulder gap (front, between pauldron edge and chest cut): 2 small pistons + 2 cables + blue dots
def gap_pt(a_deg, dc, lift):
    a_ = math.radians(a_deg); dv = ce1 * math.cos(a_) + ce2 * math.sin(a_)
    loc, n_, k_, dd = CB0.ray_cast(C0 + NCUT * dc, dv, 0.09)
    if loc is None: return None
    return loc + n_ * lift
def piston_pp(p0, p1, rb):
    ax = (p1 - p0); L = ax.length; ax.normalize(); lb = L * 0.58
    MECH.add_bm(bm_cyl(rb, lb, 20, bev=0.0003), frame(p0 + ax * (lb / 2), ax), 0)
    MECH.add_bm(bm_cyl(rb * 0.48, L - lb + 0.002, 14), frame(p0 + ax * (lb + (L - lb) / 2 - 0.001), ax), 1)
    for p, r in ((p0, rb * 1.2), (p1, rb * 0.95)): MECH.add_bm(bm_sphere(r, 14, 8), Matrix.Translation(p), 0)
    MECH.add_bm(bm_cyl(rb * 1.12, 0.0009, 20), frame(p0 + ax * (lb - 0.0005), ax), 1 if AI_TOOLS else 2)
for (a0, a1, dc, rb) in ((208, 168, 0.0075, 0.0017), (238, 200, 0.0140, 0.0015)):
    p0 = gap_pt(a0, dc, rb + 0.0004); p1 = gap_pt(a1, dc, rb + 0.0004)
    if p0 is not None and p1 is not None: piston_pp(p0, p1, rb)
for ci, (dc, lift) in enumerate(((0.0040, 0.0009), (0.0110, 0.0010))):
    pts = [gap_pt(a, dc, lift) for a in np.linspace(255, 130, 40)]
    pts = [p for p in pts if p is not None]
    if len(pts) > 4: tube_obj("Robo_ShoulderCable_%d" % ci, smooth_pts(pts, 4), 0.0008, M_DARK if ci else M_GUN)
# v5: gap dots removed
log("mechanics done")

X = V((1, 0, 0)); Y = V((0, 1, 0)); Z = V((0, 0, 1))
def ring_pts_se(C, Xa, Ya, hw, ht, e, n, a0=0.0, a1=2 * math.pi, closed=True, vflat=1.0):
    out = []
    cnt = n if closed else n + 1
    for k in range(cnt):
        a = a0 + (a1 - a0) * k / n
        c, s = math.cos(a), math.sin(a)
        x = hw * math.copysign(abs(c) ** (2.0 / e), c); y = ht * math.copysign(abs(s) ** (2.0 / e), s)
        if y < 0: y *= vflat
        out.append(C + Xa * x + Ya * y)
    return out

def loft_bm(rows, closed=True, cap0=True, cap1=True):
    bm = bmesh.new(); VV = [[bm.verts.new(p) for p in r] for r in rows]
    n = len(rows[0])
    for i in range(len(rows) - 1):
        for k in range(n if closed else n - 1):
            k2 = (k + 1) % n
            bm.faces.new((VV[i][k], VV[i][k2], VV[i + 1][k2], VV[i + 1][k]))
    if closed:
        for idx, ok in ((0, cap0), (-1, cap1)):
            if not ok: continue
            c = bm.verts.new(sum((v.co for v in VV[idx]), V()) / n)
            for k in range(n): bm.faces.new((c, VV[idx][(k + 1) % n], VV[idx][k]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return bm

def frame_xy(s, xh):
    s = s.normalized(); x = (xh - s * xh.dot(s)).normalized(); y = s.cross(x).normalized()
    return s, x, y   # y = s x x

# ------------------------------------------------------------------ 5. wrist joint + hand (v6)
# Rebuilt from scratch, fitted onto the ORIGINAL marble right hand (skeleton measured on ArmRef, scripts/c6/hand_skel.py),
# scaled x1.08 around the wrist so the armoured hand never reads smaller than the marble.
# Style cues: Figure 02 / Shadow Hand / Optimus: chamfered phalanx shells (U-section) over a darker inner link, side lugs +
# pin heads at every joint, visible knuckle drums with tendon pairs, palm = carpal + metacarpal dorsal plates and three palmar
# pads (thenar / hypothenar / distal) over a mid-grey core, opposed thumb on a CMC housing low on the thenar pad.
sys.path.insert(0, "/tmp/claude-0/-home-user-kardonov-site/cb30cd45-1b88-5b9b-b3ff-480343f6cfce/scratchpad/scripts/c6")
import hand_skel, importlib; importlib.reload(hand_skel)
HAND = Acc("Robo_Hand", [M_IVORY, M_JOINT, M_BLUE, M_STEEL])
TI, JT, GL, ST = 0, 1, 2, 3
HKS = 1.08
WR = V(hand_skel.WRIST)
def skp(p): return WR + (V(p) - WR) * HKS
FJ = {n: [skp(p) for p in pts] for n, pts in hand_skel.FINGERS.items()}
FN = ("Index", "Middle", "Ring", "Pinky")
MCPm = sum((FJ[n][0] for n in FN), V()) / 4
HS = (MCPm - WR).normalized()
HW = FJ["Pinky"][0] - FJ["Index"][0]; HW = (HW - HS * HW.dot(HS)).normalized()
HD = HW.cross(HS).normalized()                       # dorsal (back of hand), ~ -X
log("hand frame HS", tuple(round(c, 3) for c in HS), "HW", tuple(round(c, 3) for c in HW), "HD", tuple(round(c, 3) for c in HD))
def HP(s, w, d): return WR + HS * s + HW * w + HD * d
def HLc(p): q = p - WR; return q.dot(HS), q.dot(HW), q.dot(HD)
MC = {n: HLc(FJ[n][0]) for n in FN}
S_MCP = min(v[0] for v in MC.values()); S_MCPm = sum(v[0] for v in MC.values()) / 4
W_C = sum(v[1] for v in MC.values()) / 4; D_C = sum(v[2] for v in MC.values()) / 4
log("MCP local (s,w,d)", {k: tuple(round(c, 4) for c in v) for k, v in MC.items()})

class UProf(list):
    u = True          # U-section (outer path + inner path reversed): caps are built as a quad strip, not an ngon
def _bev(p, a, b, rb):
    p, a, b = np.array(p), np.array(a), np.array(b)
    return [tuple(p + (a - p) / np.linalg.norm(a - p) * rb), tuple(p + (b - p) / np.linalg.norm(b - p) * rb)]
def oct_pts(w, h, c, rb=0.00022):
    hw, hh = w / 2, h / 2; c = min(c, hw * 0.8, hh * 0.8)
    cs = [(hw, -hh + c), (hw, hh - c), (hw - c, hh), (-hw + c, hh), (-hw, hh - c), (-hw, -hh + c), (-hw + c, -hh), (hw - c, -hh)]
    out = []
    for i in range(8): out += _bev(cs[i], cs[i - 1], cs[(i + 1) % 8], rb)
    return out
def ushell_pts(w, h, c, t, yc, rb=0.00022):
    """dorsal cap section: outer chamfered top from (w/2,yc) over to (-w/2,yc), back along the inner face (thickness t)"""
    def half(w_, h_, c_):
        hw, hh = w_ / 2, h_ / 2; c_ = min(c_, hw * 0.8, (hh - yc) * 0.8)
        cs = [(hw, yc), (hw, hh - c_), (hw - c_, hh), (-hw + c_, hh), (-hw, hh - c_), (-hw, yc)]
        out = [cs[0]]
        for i in range(1, 5): out += _bev(cs[i], cs[i - 1], cs[i + 1], rb)
        return out + [cs[5]]
    return UProf(half(w, h, c) + half(w - 2 * t, h - 2 * t, max(c - 0.6 * t, 0.0004))[::-1])
def uarch_pts(w, h, t, yc, arch=0.30, cf=0.16, n=10, rb=0.00022):
    """dorsal shell section with an ARCHED top: straight side walls, one crisp chamfer each side, smooth arch across,
    then back along the inner face (thickness t). arch = arch rise / h, cf = chamfer / w"""
    def half(w_, h_):
        hw, hh = w_ / 2, h_ / 2; ah = arch * h_; ys = hh - ah; c = cf * w_
        pts = [(hw, yc)] + _bev((hw, ys - 0.6 * c), (hw, yc), (hw - c, ys + 0.25 * ah), rb)
        for i in range(n + 1):
            x = (hw - c) * (1 - 2 * i / n); u = x / (hw - c)
            pts.append((x, ys + 0.25 * ah + 0.75 * ah * math.sqrt(max(0.0, 1 - u * u))))
        pts += _bev((-hw, ys - 0.6 * c), (-hw + c, ys + 0.25 * ah), (-hw, yc), rb) + [(-hw, yc)]
        return pts
    return UProf(half(w, h) + half(w - 2 * t, h - 2 * t)[::-1])
def loft_rows(rows, cap=True, ustrip=False):
    bm = bmesh.new(); VV = [[bm.verts.new(p) for p in r] for r in rows]; n = len(rows[0])
    for i in range(len(rows) - 1):
        for k in range(n):
            k2 = (k + 1) % n; bm.faces.new((VV[i][k], VV[i][k2], VV[i + 1][k2], VV[i + 1][k]))
    if cap and ustrip:
        m = n // 2
        for R_ in (VV[0], VV[-1]):
            for k in range(m - 1): bm.faces.new((R_[k], R_[k + 1], R_[n - 2 - k], R_[n - 1 - k]))
    elif cap: bm.faces.new(VV[0][::-1]); bm.faces.new(VV[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return bm
def add(bm, mi):
    HAND.add_bm(bm, Matrix(), mi)
def prism(A, t, X, Y, stations, prof, mi):
    """stations: (s, kx, ky, dy); prof(s) -> 2D pts; section scaled (kx,ky) about its own origin then shifted dy"""
    rows = [[A + t * s + X * (x * kx) + Y * (y * ky + dy) for x, y in prof(s)] for s, kx, ky, dy in stations]
    add(loft_rows(rows, ustrip=getattr(prof(stations[0][0]), 'u', False)), mi)
def endst(s0, s1, ch=0.0007, k=0.86, n=4):
    mid = [s0 + ch + (s1 - s0 - 2 * ch) * i / n for i in range(n + 1)]
    return [(s0, k, k, 0.0)] + [(s, 1, 1, 0.0) for s in mid] + [(s1, k, k, 0.0)]
def cyl(p, axis, r, h, mi, segs=28, bev=0.0):
    HAND.add_bm(bm_cyl(r, h, segs, bev=bev), frame(p, axis), mi)

def joint_parts(A, X, Y, w, h, lug=True):
    """knuckle drum (joint grey) + titanium side lugs + pin heads on the hinge axis X"""
    cyl(A, X, 0.27 * h, 0.72 * w, JT, 28, bev=0.0003)
    for sg in (-1, 1):
        if lug: cyl(A + X * sg * (w / 2 - 0.0004), X, 0.27 * h, 0.0007, TI, 32, bev=0.0002)
        cyl(A + X * sg * (w / 2 - 0.0001), X, 0.095 * h, 0.0006, JT, 20, bev=0.00012)

def phalanx6(A, B, hinge, dhint, w0, w1, h0, g0, g1, tip=False, pad=True, lug=True):
    t = (B - A).normalized(); L = (B - A).length
    X = (hinge - t * hinge.dot(t)).normalized(); Y = X.cross(t).normalized()
    if Y.dot(dhint) < 0: Y = -Y; X = -X
    W = lambda s: w0 + (w1 - w0) * min(max(s / L, 0.0), 1.0)
    Hh = lambda s: h0 * W(s) / w0
    shell = lambda s: uarch_pts(W(s), Hh(s), 0.0010, -0.16 * Hh(s), arch=0.26, cf=0.13)
    s0, s1 = g0, L - g1
    kU = 1 - 0.8 * 0.0010 / w0           # thin U-shell: end chamfer must stay inside the wall thickness
    st = endst(s0, s1, 0.0005, kU) if not tip else endst(s0, s1, 0.0005, kU)[:-1]
    if tip:                                           # rounded, slightly palmar-curving tip cap
        R = 0.42 * Hh(s1)
        for q in (0.25, 0.5, 0.72, 0.88, 1.0):
            k = max(0.24, math.cos(q * math.pi / 2) ** 0.55)
            st.append((s1 + R * math.sin(q * math.pi / 2), k, k, -0.10 * Hh(s1) * q))
    # gentle crown along the length (shell rises over the middle of the phalanx, like a real dorsal plate)
    st = [(s_, kx * (1 + 0.025 * math.sin(math.pi * min(max((s_ - s0) / max(s1 - s0, 1e-6), 0), 1))),
           ky * (1 + 0.07 * math.sin(math.pi * min(max((s_ - s0) / max(s1 - s0, 1e-6), 0), 1))), dy) for s_, kx, ky, dy in st]
    prism(A, t, X, Y, st, shell, TI)
    # inner link (darker mechanism visible in the gaps and under the shell)
    s_end = (s1 + 0.25 * Hh(s1)) if tip else L
    prism(A, t, X, Y, [(0.0, 1, 1, 0), (s_end, 1, 1, 0)], lambda s: [(x, y - 0.10 * Hh(s)) for x, y in oct_pts(0.56 * W(s), 0.60 * Hh(s), 0.12 * Hh(s))], JT)
    if pad:                                           # palmar pad (titanium), separate from the shell by a dark seam
        p0, p1 = 0.20 * L, (s1 + 0.20 * Hh(s1)) if tip else 0.80 * L
        pst = endst(p0, p1, 0.0006, 0.80)
        prism(A, t, X, Y, pst, lambda s: [(x, y - 0.365 * Hh(s)) for x, y in oct_pts(0.80 * W(s), 0.26 * Hh(s), 0.10 * Hh(s))], TI)
    joint_parts(A, X, Y, w0, h0, lug)
    return X, Y

def rotv(v, ax, deg): return (Matrix.Rotation(math.radians(deg), 3, ax) @ v).normalized()

# ---- fingers: marble directions, anatomical ratios (prox 1 : mid 0.62 : dist 0.47), cascade (index least .. little most)
FDIM = {"Index": (0.0150, 0.0124), "Middle": (0.0156, 0.0128), "Ring": (0.0148, 0.0122), "Pinky": (0.0130, 0.0108)}
FADJ = {"Index": -9.0, "Middle": -4.0, "Ring": 0.0, "Pinky": 4.0}
TIPS = {}; FINF = {}
for nm in FN:
    M_, P_, D_, T_ = FJ[nm]
    t1 = (P_ - M_).normalized(); t2 = (D_ - P_).normalized(); t3 = (T_ - D_).normalized()
    hinge = t1.cross(t2).normalized()
    Lf1 = (P_ - M_).length; Lf2 = 0.62 * Lf1; Lf3 = 0.47 * Lf1
    t2 = rotv(t2, hinge, FADJ[nm]); t3 = rotv(t3, hinge, 2 * FADJ[nm])
    J = [M_, M_ + t1 * Lf1]; J.append(J[1] + t2 * Lf2); J.append(J[2] + t3 * Lf3)
    w0, w1 = FDIM[nm]; h = 0.86 * w0
    ws = [w0, w0 + (w1 - w0) * 0.45, w0 + (w1 - w0) * 0.75, w1]
    dh = HD
    for i in range(3):
        last = (i == 2)
        hh = 0.86 * ws[i]
        X, Y = phalanx6(J[i], J[i + 1], hinge, dh, ws[i], ws[i + 1], hh, 0.24 * hh, 0.22 * 0.86 * ws[i + 1], tip=last)
        dh = Y
        if i == 0: FINF[nm] = (J[0], t1, X, Y, ws[0], hh)
    TIPS[nm] = J[3]

# ---- thumb: CMC housing low on the thenar side, metacarpal + 2 phalanges, nail plane rotated 55 deg out of the palm plane
TH = FJ["Thumb"]
TN = (HD * math.cos(math.radians(55)) - HW * math.sin(math.radians(55))).normalized()   # thumb dorsal (nail) direction
tm = (TH[1] - TH[0]).normalized(); tp = (TH[2] - TH[1]).normalized(); td = (TH[3] - TH[2]).normalized()
th_hinge = tm.cross(TN).normalized()
Lm = (TH[1] - TH[0]).length; Lp = (TH[2] - TH[1]).length; Ld = 0.66 * Lp
TJ = [TH[0], TH[1], TH[1] + tp * Lp]; TJ.append(TJ[2] + td * Ld)
tws = [0.0182, 0.0168, 0.0158, 0.0140]
dh = TN
for i in range(3):
    hh = 0.84 * tws[i]
    if i == 0:          # metacarpal: no free shell - it is wrapped by the thenar block (below); keep its frame
        X = (th_hinge - tm * th_hinge.dot(tm)).normalized(); Y = X.cross(tm).normalized()
        if Y.dot(dh) < 0: Y = -Y; X = -X
        TX0, TY0 = X, Y; dh = Y; continue
    X, Y = phalanx6(TJ[i], TJ[i + 1], th_hinge, dh, tws[i], tws[i + 1], hh, (0.42 if i == 0 else 0.24) * hh, 0.22 * 0.84 * tws[i + 1],
                    tip=(i == 2), lug=(i > 0))
    dh = Y
TIPS["Thumb"] = TJ[3]
# CMC base housing: titanium ring around a grey drum, axis = thumb hinge, seated on the thenar pad
cmc = TJ[0]
cyl(cmc, TX0, 0.0056, 0.0120, JT, 36, bev=0.0005)                     # saddle drum (grey)
for sg in (-1, 1):
    cyl(cmc + TX0 * sg * 0.0058, TX0, 0.0072, 0.0012, TI, 40, bev=0.0004)  # titanium bearing cheeks
    cyl(cmc + TX0 * sg * 0.0066, TX0, 0.0026, 0.0007, JT, 24, bev=0.0002)  # pin heads

# ---- palm
s_end = S_MCP - 0.0005
def lerp(a, b, f): return a + (b - a) * f
PW0, PW1 = 0.0430, (MC["Pinky"][1] - MC["Index"][1]) + 0.0125
def palm_cw(s):
    f = min(max(s / S_MCPm, 0.0), 1.0)
    return lerp(0.0, W_C, f), lerp(0.0, D_C, f), lerp(PW0, PW1, f ** 0.8)
def palm_prism(s0, s1, prof, mi, wc_off=0.0, flip=False, n=6, ch=0.0006, k=1.0):
    rows = []
    for s, kx, ky, dy in endst(s0, s1, ch, k, n):
        wc, dc, pw = palm_cw(s); sg = -1 if flip else 1
        rows.append([HP(s, wc + wc_off + x * kx, dc + sg * (y * ky)) for x, y in prof(s, pw)])
    add(loft_rows(rows, ustrip=getattr(prof(s0, 0.05), 'u', False)), mi)
# core (inner mechanism, mid grey)
palm_prism(-0.004, S_MCP - 0.0015, k=0.9, prof=lambda s, pw: oct_pts(pw - 0.002, 0.0170 - 0.0040 * min(max((s - 0.030) / (S_MCP - 0.030), 0), 1), 0.0050), mi=JT)
# dorsal: carpal plate + metacarpal plate (titanium), chamfered, a 1.4 mm seam between them
DPL = lambda s, pw: uarch_pts(pw + 0.0030, 0.0250, 0.0022, -0.0004, arch=0.18, cf=0.06)
palm_prism(0.0020, 0.0150, DPL, TI)
S_MP1 = s_end - 0.0046
palm_prism(0.0164, S_MP1, DPL, TI)       # metacarpal plate (one sculpted arched shell)
# knuckle caps (Figure-02 style): one short arched cap per finger over its MCP drum, small gaps between them
for nm in FN:
    A, t1, X, Y, w0, hh = FINF[nm]
    prism(A, t1, X, Y, endst(-0.0042, 0.0016, 0.0005, 0.94, 3),
          lambda s_, w0=w0, hh=hh: uarch_pts(w0 * 1.04, hh * 1.45, 0.0011, 0.02 * hh, arch=0.30, cf=0.12), TI)
# palmar pads (flipped U-shells): distal pad under the knuckles, hypothenar (little-finger side), thenar (thumb side)
palm_prism(S_MP1 - 0.0090, s_end - 0.0010, lambda s, pw: ushell_pts(pw + 0.0026, 0.0232, 0.0040, 0.0020, 0.0012), TI, flip=True)
palm_prism(0.0040, S_MP1 - 0.0104, lambda s, pw: ushell_pts(0.55 * pw, 0.0232, 0.0040, 0.0020, 0.0012), TI, wc_off=+0.22 * PW1, flip=True)
palm_prism(0.0030, S_MP1 - 0.0104, lambda s, pw: ushell_pts(0.44 * pw, 0.0262, 0.0045, 0.0020, 0.0012), TI, wc_off=-0.27 * PW1, flip=True)
# thenar block: faceted convex hull wrapping the thumb metacarpal into the palm (thumb grows out of the thenar mass,
# CMC housing left exposed at its root, MCP drum exposed at its end)
hp = []
for s_ in (0.009, 0.017, 0.025, 0.033):
    wc, dc, pw = palm_cw(s_)
    for w_ in (-pw / 2 + 0.002, -pw / 2 + 0.008, -0.003):
        hp.append(HP(s_, wc + w_, dc - 0.0122))
for f_ in (0.22, 0.40, 0.60, 0.80):
    c_ = TJ[0] + tm * (Lm * f_); R_ = 0.0080 - 0.0014 * f_
    for k_ in range(12):
        a_ = 2 * math.pi * (k_ + 0.5) / 12
        hp.append(c_ + (TX0 * math.cos(a_) + TY0 * math.sin(a_)) * R_)
bmh = bmesh.new()
for p_ in hp: bmh.verts.new(p_)
bmesh.ops.convex_hull(bmh, input=bmh.verts[:])
bmesh.ops.bevel(bmh, geom=[e for e in bmh.edges if e.calc_face_angle(0) > 0.35], offset=0.0006, segments=2, affect='EDGES', clamp_overlap=True)
bmesh.ops.recalc_face_normals(bmh, faces=bmh.faces[:])
bmesh.ops.dissolve_degenerate(bmh, dist=1e-6, edges=bmh.edges[:])
add(bmh, TI)
# back-of-hand disc: small, integrated (titanium bezel, grey well, closed neon ring, small blue core)
s_disc = 0.5 * (0.0164 + S_MP1)
wc, dc, pw = palm_cw(s_disc)
DISC_P = HP(s_disc, wc, dc + 0.0125); DISC_N = HD
cyl(DISC_P + DISC_N * 0.0004, DISC_N, 0.0050, 0.0012, TI, 48, bev=0.0004)
cyl(DISC_P + DISC_N * 0.0009, DISC_N, 0.0040, 0.0008, JT, 48)
HAND.add_bm(bm_torus(0.0029, NRAD, 48, 8), frame(DISC_P + DISC_N * 0.0013, DISC_N, HS), GL)
cyl(DISC_P + DISC_N * 0.0012, DISC_N, 0.0016, 0.0008, GL, 32, bev=0.0002)
# tendon pairs: from under the metacarpal plate, over each knuckle drum, into the proximal shell
for nm in FN:
    A, t1, X, Y, w0, hh = FINF[nm]
    for sg in (-1, 1):
        sw = X * sg * 0.0021
        sa, wa, da = HLc(A)
        wt = max(-0.0175, min(0.0175, wa))          # stay inside the dorsal plate walls
        p0 = HP(S_MP1 - 0.006, wt, D_C + 0.0090) + sw
        p1 = HP(S_MP1 + 0.0005, 0.5 * (wt + wa), D_C + 0.0082) + sw
        p2 = A + Y * (0.30 * hh + 0.0006) + sw
        p3 = A + t1 * (0.30 * hh + 0.004) + Y * (0.30 * hh) + sw
        pts = []
        for a_, b_ in ((p0, p1), (p1, p2), (p2, p3)):
            for i in range(8): pts.append(a_.lerp(b_, i / 8))
        pts.append(p3)
        tube_obj("Robo_HandTendon_%s_%d" % (nm, sg > 0), smooth_pts(pts, 4), 0.00042, M_JOINT)

# ---- wrist joint: compact ribbed bearing from the forearm plate ends to the palm core
NJ = 48; J0 = E + u2 * (WJ0 - 0.0010)
r0 = []
for k in range(NJ):
    th = 2 * math.pi * k / NJ; A, d, r = radial(1, WJ0 - 0.0010, th); r0.append((d, r))
rr = np.array([r for _, r in r0]); rr = fill_nan(rr)
for _ in range(3): rr = (np.roll(rr, 1) + 2 * rr + np.roll(rr, -1)) / 4
P0r = [J0 + d * (rr[k] - 0.0016) for k, (d, _) in enumerate(r0)]
C1 = HP(-0.003, 0.0, 0.0)
P1r = []
for k, (d, _) in enumerate(r0):
    dd = d - HS * d.dot(HS); a = math.atan2(dd.dot(HD), dd.dot(HW))
    # ray from the centre to the (core-sized) octagon at that angle
    hw, hh = (PW0 - 0.002) / 2 + 0.0008, 0.0095 + 0.0008; ca, sa_ = abs(math.cos(a)) + 1e-9, abs(math.sin(a)) + 1e-9
    rad = min(hw / ca, hh / sa_, 1.0 / (ca / hw + sa_ / hh) * 1.45)
    P1r.append(C1 + (HW * math.cos(a) + HD * math.sin(a)) * rad)
NR = 30; jrows = []
for i in range(NR + 1):
    f = i / NR; fs = f * f * (3 - 2 * f)
    pts = [P0r[k].lerp(P1r[k], fs) for k in range(NJ)]
    c = sum(pts, V()) / NJ
    rib = 0.0
    if 0.15 < f < 0.85:
        q = (f - 0.15) / 0.70; rib = 0.5 + 0.5 * math.cos(2 * math.pi * 2 * q)
    m = 1.0 - 0.05 * math.sin(math.pi * f) + 0.03 * rib * math.sin(math.pi * f)
    jrows.append([c + (p - c) * m for p in pts])
JOINT = Acc("Robo_WristJoint", [M_JOINT]); JOINT.add_bm(loft_bm(jrows), Matrix(), 0)
log("hand done; tips", {k: tuple(round(c, 3) for c in v) for k, v in TIPS.items()})
for acc in (MECH, EMITTER, HAND, JOINT):
    acc.build(32)

# ------------------------------------------------------------------ 6. headband (round 3): sampled from the head surface
log("headband")
HC = V((-0.031, -0.002, 0.0)); FACE = V((0.81, -0.59, 0)).normalized(); fa = math.atan2(FACE.y, FACE.x)
NB = 360; BH = 0.0095; BT = 0.0022; OFF = 0.0008
def zband(th): return 0.9425 + 0.0045 * math.cos(th - fa)
TH = np.array([-math.pi + (i + 0.5) * 2 * math.pi / NB for i in range(NB)])
HS = np.linspace(-0.5, 0.5, 7) * BH
RS = np.full((NB, len(HS)), np.nan)
for i, th in enumerate(TH):
    d = V((math.cos(th), math.sin(th), 0)); zc = zband(th)
    for j, h in enumerate(HS):
        o = HC + V((0, 0, zc + h)) + d * 0.16
        loc, n_, k_, dd = MB0.ray_cast(o, -d, 0.16)
        if loc is not None: RS[i, j] = 0.16 - dd
def circ_smooth(a, it):
    a = a.copy()
    for _ in range(it): a = (np.roll(a, 1) + 2 * a + np.roll(a, -1)) / 4
    return a
RS = np.where(np.isnan(RS), np.nanmedian(RS), RS)
R60 = np.percentile(RS, 25, axis=1)
RLO = np.percentile(RS[:, :3], 50, axis=1)          # lower half (forehead skin at the front)
# slope dr/dh from a line fit, clamped (top edge leans in following the skull, never flares out)
hc = HS - HS.mean(); SL = (RS - RS.mean(1, keepdims=True)) @ hc / (hc @ hc)
SL = np.clip(circ_smooth(np.clip(SL, -0.6, 0.2), 40), -0.40, 0.0)
front = np.cos(TH - fa) > math.cos(math.radians(40))
RB = np.where(front, np.minimum(R60, RLO + 0.0015), R60)
RB = circ_smooth(RB, 50)
RB = np.where(front, np.maximum(RB, circ_smooth(RLO, 50) - 0.0004), RB)      # never sink into smooth skin (forehead)
log("band radius", RB.min(), RB.max(), "slope", SL.min(), SL.max())

def bpoint(th, h, depth):
    i = ((th + math.pi) / (2 * math.pi) * NB - 0.5) % NB
    r = float(np.interp(i, np.arange(NB + 1), np.append(RB, RB[0])))
    sl = float(np.interp(i, np.arange(NB + 1), np.append(SL, SL[0])))
    d = V((math.cos(th), math.sin(th), 0))
    cf = max(0.0, math.cos(th - fa)); off_ = -0.0016 + (OFF + 0.0016) * min(1.0, cf / 0.6) ** 2
    return HC + d * (r + off_ + sl * h + depth) + V((0, 0, zband(th) + h)), (d - Z * sl).normalized()

def band_ring(name, d0, d1, h0, h1, m, bev=0.0004):
    bmb = bmesh.new(); rings = []
    for i in range(NB):
        th = TH[i]
        prof = [(d0, h0), (d1, h0), (d1, h1), (d0, h1)]
        rings.append([bmb.verts.new(bpoint(th, h, dp)[0]) for dp, h in prof])
    for i in range(NB):
        a, b = rings[i], rings[(i + 1) % NB]
        for k in range(4): bmb.faces.new((a[k], b[k], b[(k + 1) % 4], a[(k + 1) % 4]))
    bmb.normal_update(); bmesh.ops.recalc_face_normals(bmb, faces=bmb.faces)
    me = D.meshes.new(name); bmb.to_mesh(me); bmb.free(); me.materials.append(m); finish_mesh(me, 50)
    ob = link(D.objects.new(name, me))
    mm = ob.modifiers.new("bev", 'BEVEL'); mm.width = bev; mm.segments = 2; mm.limit_method = 'ANGLE'
    return ob
band_ring("Neuro_Band", 0.0, BT, -BH / 2, BH / 2, M_NGOLD)
band_ring("Neuro_Band_LipTop", BT - 0.0002, BT + 0.0008, BH / 2 - 0.0013, BH / 2, M_NGOLD, 0.0003)
band_ring("Neuro_Band_LipBot", BT - 0.0002, BT + 0.0008, -BH / 2, -BH / 2 + 0.0013, M_NGOLD, 0.0003)
band_ring("Neuro_Band_Glow", BT - 0.0003, BT + 0.0004, -0.0024, 0.0024, M_AMBER, 0.0002)

NEURO = Acc("Neuro_Modules", [M_NGOLD, M_NGUN, M_LENS])
NGLOW = Acc("Neuro_Modules_Glow", [M_RING])
for nm, off, rr in (("Front", 0.0, 0.0105), ("TempleL", math.radians(50), 0.0082),
                    ("TempleR", math.radians(-50), 0.0082), ("Back", math.pi, 0.0092)):
    th = fa + off
    p, n = bpoint(th, 0.0, BT - 0.0004)
    tang = Z.cross(n).normalized(); up = n.cross(tang).normalized()
    NEURO.add_bm(bm_cyl(rr, 0.0034, 56, bev=0.0010), frame(p + n * 0.0017, n, up), 0)
    NEURO.add_bm(bm_cyl(rr * 0.80, 0.0010, 56), frame(p + n * 0.0033, n, up), 1)
    NEURO.add_bm(bm_torus(rr * 0.92, rr * 0.07, 56, 8), frame(p + n * 0.0033, n, up), 0)
    NGLOW.add_bm(bm_torus(rr * 0.64, rr * 0.10, 56, 10), frame(p + n * 0.0038, n, up), 0)
    NEURO.add_bm(bm_sphere(rr * 0.42, 32, 16), frame(p + n * 0.0036, n, up) @ Matrix.Diagonal((1, 1, 0.40, 1)), 2)
    for sg in (-1, 1):
        NEURO.add_bm(bm_cube(0.0030, 0.0030, BH * 1.04, bev=0.0005, segs=2),
                     frame(p + tang * sg * (rr + 0.0011) + n * 0.0008, up, n), 1)
NEURO.build(35); NGLOW.build(35)
log("headband done")

# ------------------------------------------------------------------ cleanup / save
for o in (ARMREF, SMOOTH):
    me = o.data; D.objects.remove(o, do_unlink=True); D.meshes.remove(me)
SCULPT["cyber"] = 6
# v5: world = site background #0f0f12 (after AgX: linear 0.0078/0.0098 renders as 15,15,18)
SC.world.node_tree.nodes["Background"].inputs[0].default_value = (0.0078, 0.0078, 0.0098, 1)
# v6: reflection-only environment. Camera rays still see the site background #0f0f12; every other ray (reflections,
# probe capture) sees a soft light-grey vertical gradient, so the satin titanium never mirrors black.
def setup_world(env_gain=None):
    import os as _o
    g = float(_o.environ.get("ENV_GAIN", "1.0")) if env_gain is None else env_gain
    W_ = SC.world; W_.use_nodes = True; N, L_ = W_.node_tree.nodes, W_.node_tree.links
    for n in list(N): N.remove(n)
    out = N.new("ShaderNodeOutputWorld"); bgc = N.new("ShaderNodeBackground"); bge = N.new("ShaderNodeBackground")
    bgc.inputs[0].default_value = (0.0078, 0.0078, 0.0098, 1); bgc.name = "Background"
    tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); rmp = N.new("ShaderNodeValToRGB")
    L_.new(tc.outputs["Generated"], sep.inputs[0]); L_.new(sep.outputs["Z"], rmp.inputs[0])
    # Generated z in [-1,1] for the world -> ramp position = z (0..1 covers the upper hemisphere; below horizon clamps dark)
    # soft light-grey band around the horizon (what vertical metal mirrors), dark zenith/ground: the floor and the tops of
    # the marble (cosine-weighted, mostly see the zenith) are barely lifted
    cr = rmp.color_ramp; cr.elements[0].position = 0.0; cr.elements[0].color = (0.05, 0.05, 0.055, 1)
    cr.elements[1].position = 0.85; cr.elements[1].color = (0.03, 0.03, 0.035, 1)
    for p_, c_ in ((0.08, 0.30), (0.26, 0.46), (0.48, 0.30), (0.64, 0.10)):
        e = cr.elements.new(p_); e.color = (c_, c_ * 1.02, c_ * 1.07, 1)
    L_.new(rmp.outputs["Color"], bge.inputs[0]); bge.inputs[1].default_value = g
    lp = N.new("ShaderNodeLightPath"); mix = N.new("ShaderNodeMixShader")
    L_.new(lp.outputs["Is Camera Ray"], mix.inputs[0]); L_.new(bge.outputs[0], mix.inputs[1]); L_.new(bgc.outputs[0], mix.inputs[2])
    L_.new(mix.outputs[0], out.inputs[0])
    try: W_.sun_threshold = 100.0
    except Exception: pass
setup_world()
# compositor preview glare (if the file has one): softer
sys.path.insert(0, "/tmp/claude-0/-home-user-kardonov-site/cb30cd45-1b88-5b9b-b3ff-480343f6cfce/scratchpad/scripts/c6")
from glowcomp import setup_glow, add_aov
import os as _os
AMB = float(_os.environ.get("AMBER_AOV", "1.4"))
for _m in (M_AMBER, M_RING): add_aov(_m, (1.0, 0.36, 0.04), AMB)
add_aov(M_LENS, (1.0, 0.38, 0.05), AMB * 0.5)
# (materials without an AOV output write 0 -> only the headband glow parts bloom amber)
setup_glow(SC)
for coll in (D.meshes, D.curves, D.materials):
    for m in list(coll):
        if m.users == 0: coll.remove(m)
log("objects in Cyber", len(COL.objects) if COL else None)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
log("saved", OUT)
