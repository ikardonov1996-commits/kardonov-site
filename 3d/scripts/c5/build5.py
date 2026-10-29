# Cyber David v5 (round-5: AI_Titanium plating, clean neon layout, amber headband glow; on top of v4): rebuild robotic arm (layered plates, mechanics, glow, articulated hand) and the neuro headband.
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
M_BLUE = mat("Cyber_GlowBlue", (0.05, 0.40, 1.0), rough=0.3, emis=(0.02, 0.30, 1.0), estr=4.0, vp=(0.25, 0.66, 1.0))
M_BLUE_HOT = mat("Cyber_GlowBlueHot", (0.2, 0.6, 1.0), rough=0.3, emis=(0.03, 0.34, 1.0), estr=6.0, vp=(0.5, 0.8, 1.0))
M_NGOLD = mat("Neuro_Gold", (1.0, 0.58, 0.20), metal=1.0, rough=0.28)
M_AMBER = mat("Neuro_GlowAmber", (0.05, 0.015, 0.0), rough=0.3, emis=(1.0, 0.36, 0.04), estr=4.0, vp=(1.0, 0.6, 0.2))
M_RING = mat("Neuro_GlowRing", (0.05, 0.015, 0.0), rough=0.3, emis=(1.0, 0.36, 0.04), estr=5.0, vp=(1.0, 0.5, 0.1))
import os
# v5: ONE shared light cool-grey AI metal (shared with chisel + windlass handle; parameters untouched)
sys.path.insert(0, "/tmp/claude-0/-home-user-kardonov-site/cb30cd45-1b88-5b9b-b3ff-480343f6cfce/scratchpad/scripts")
from mat_ai_titanium import ai_titanium
M_NGUN = M_GUN                       # headband bezels keep the v4 dark gunmetal (headband unchanged)
M_IVORY = ai_titanium()              # all plates, hand shells, finger covers
# joints / mechanics in the gaps: same family, a step darker so the plates read as separate parts
M_JOINT = mat("AI_Titanium_Joint", (0.30, 0.32, 0.355), metal=1.0, rough=0.40)
M_GUN = M_JOINT
M_GOLD = M_JOINT                     # arm trim slot (plate rims, hinge, emitter bezel) -> darker titanium, NOT neon
M_DARK = mat("AI_Rubber", (0.06, 0.065, 0.075), rough=0.55)   # cables / finger axles: dark grey, not black
PLATE_TRIM = 0
NRAD = 0.00075                       # ONE neon line thickness for the whole arm (tube radius, m)
AI_TOOLS = True
print("AI materials:", M_IVORY.name, M_JOINT.name, flush=True)
M_LENS = mat("Neuro_Lens", (0.30, 0.10, 0.02), metal=0.3, rough=0.12, emis=(1.0, 0.38, 0.05), estr=1.2)

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

# elbow: hinge (side discs, see mechanics) + short ribbed core, one blue ring on the forearm side
for k in (-2, -1, 1, 2):
    nn = (nEl + (u2 - u1) * (k * 0.06)).normalized()
    ring("Robo_ElbowRib_%d" % (k + 2), E + nEl * (k * 0.0034), nn, E, 0.0006, 0.0009, M_GUN)
ELB_PTS = ring_pts(E, nEl, E, 0.0012)
tube_obj("Robo_Glow_ElbowRing", ELB_PTS, NRAD, M_BLUE, closed=True)
# wrist: one compact joint - blue ring at the plate ends
WR_C = E + u2 * (WJ0 - 0.0020)
WR_PTS = ring_pts(WR_C, u2, W, 0.0010)
tube_obj("Robo_Glow_WristRing", WR_PTS, NRAD, M_BLUE, closed=True)
# shoulder: neon ring recessed into the marble cut (closed loop, boundary marble / machine)
tube_obj("Robo_Glow_Collar", smooth_pts(CL, 2, closed=True)[::2], NRAD, M_BLUE, closed=True)

# ---- channels (v5): exactly two, each a single seam channel per segment.
# start: tucked >=6 mm under the lower edge of the overlapping plate above (fold); end: runs INTO the joint ring
def chan_to_ring(name, th, s0, plane_c, plane_n, ring, off=0.0018, dip=0.010):
    raw = chan_line(th, s0, s0 + 0.25, off, steps=400)
    pts = []
    for p in raw:
        if (p - plane_c).dot(plane_n) >= -0.0005: break
        pts.append(p)
    tgt = min(ring, key=lambda q: (q - pts[-1]).length)          # nearest point on the ring curve
    # last `dip` metres: blend the path down onto the ring so the tube merges into it
    acc = 0.0; k = len(pts) - 1
    while k > 0 and acc < dip: acc += (pts[k] - pts[k - 1]).length; k -= 1
    head = pts[:k + 1]; tail = pts[k + 1:]
    a = head[-1]; n_ = len(tail) + 1
    for i, p in enumerate(tail):
        f = (i + 1) / n_; f = f * f * (3 - 2 * f)
        tail[i] = p.lerp(a.lerp(tgt, (i + 1) / n_), f)
    pts = smooth_pts(head + tail + [tgt], 3)
    ob = tube_obj(name, pts, NRAD, M_BLUE)
    ob.data.use_fill_caps = True
    log(name, "end gap to ring %.5f" % (pts[-1] - tgt).length, "len %.3f" % sum((pts[i+1]-pts[i]).length for i in range(len(pts)-1)))
    return ob
# upper arm: front seam (UpperLat | UpperFront), from under the Shoulder2 plate down into the elbow ring
GLOW.append(chan_to_ring("Robo_Glow_ChannelUpper", 76.5, 0.064, E, nEl, ELB_PTS))
# forearm: lateral seam (ForeLat | ForeBack), from under the ForeLatUp plate down into the wrist ring
GLOW.append(chan_to_ring("Robo_Glow_ChannelFore", -1.0, L0 + 0.046, WR_C, u2, WR_PTS))
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

# ------------------------------------------------------------------ 5. wrist joint + hand (round 3)
HAND = Acc("Robo_Hand", [M_IVORY, M_GUN, M_GOLD, M_BLUE, M_STEEL, M_DARK])
X = V((1, 0, 0)); Y = V((0, 1, 0)); Z = V((0, 0, 1))
# hand frame measured from the marble hand: width axis (index -> pinky) and dorsal axis are diagonal in XY
XW = V((-0.7071, 0.7071, 0.0)); DD = V((-0.7071, -0.7071, 0.0)); W0 = V((-0.175, -0.002, 0.0))
def HL(w, d, z): return W0 + XW * w + DD * d + Z * z

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

# ---- palm (tapered, slightly curved shell): measured from the marble hand
PLEN = 30
HK = 1.25   # client: hand scaled up around the wrist pivot to match the armoured arm
def palm_sec(u):
    w = -0.006 - 0.009 * u; d = 0.0025 - 0.002 * u - 0.0025 * math.sin(math.pi * u) * 0.0  # centre line
    z = 0.5005 - 0.0525 * u
    C = HL(w, d, z) - DD * 0.0035 * u * u          # gentle curl toward the palm side
    hw = 0.0116 + 0.0080 * (u ** 0.75) - 0.0008 * u ** 4; ht = 0.0074 - 0.0010 * u + 0.0012 * math.sin(math.pi * u)
    return C, hw, ht
def palm_axis(u):
    a, _, _ = palm_sec(max(0.0, u - 0.02)); b, _, _ = palm_sec(min(1.0, u + 0.02)); return (b - a).normalized()
def palm_ring(u, grow=0.0, e=2.2, n=48, a0=0.0, a1=2 * math.pi, closed=True):
    C, hw, ht = palm_sec(u); s = palm_axis(u); s, Xa, Ya = frame_xy(s, XW)
    if Ya.dot(DD) < 0: Ya = -Ya
    return ring_pts_se(C, Xa, Ya, hw + grow, ht + grow, e, n, a0, a1, closed, vflat=0.92)
rows = [palm_ring(i / PLEN) for i in range(PLEN + 1)]
HAND.add_bm(loft_bm(rows), Matrix(), 1)                     # gunmetal palm body

R = math.radians
# Acc.add_bm assigns one material index; use a small wrapper keeping per-face indices
def add_bm_keep(acc, bm):
    off = len(acc.V); acc.V += [tuple(v.co) for v in bm.verts]; bm.verts.index_update()
    for f in bm.faces:
        acc.F.append([off + v.index for v in f.verts]); acc.M.append(f.material_index)
    bm.free()
def shell2(u0, u1, a0, a1, grow, thick, mi=0, rim=2, nu=26, nv=24, domeh=0.0006):
    bm = bmesh.new(); VV = []
    for i in range(nu + 1):
        row = []
        for k in range(nv + 1):
            x = -1 + 2 * i / nu; y = -1 + 2 * k / nv
            mx = max(abs(x), abs(y)); n4 = (abs(x) ** 2.6 + abs(y) ** 2.6) ** (1 / 2.6)
            sx, sy = (x * mx / n4, y * mx / n4) if n4 > 0 else (0.0, 0.0)
            u = (u0 + u1) / 2 + sx * (u1 - u0) / 2; a = (a0 + a1) / 2 + sy * (a1 - a0) / 2
            dome = domeh * (1 - mx * mx)
            row.append(bm.verts.new(palm_ring(u, grow + dome, n=1, a0=a, a1=a, closed=False)[0]))
        VV.append(row)
    for i in range(nu):
        for k in range(nv):
            f = bm.faces.new((VV[i][k], VV[i][k + 1], VV[i + 1][k + 1], VV[i + 1][k]))
            f.material_index = rim if (i == 0 or k == 0 or i == nu - 1 or k == nv - 1) else mi
    bm.normal_update()
    C, _, _ = palm_sec((u0 + u1) / 2)
    if sum((f.calc_center_median() - C).dot(f.normal) for f in bm.faces) < 0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
    bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=thick)
    add_bm_keep(HAND, bm)
shell2(0.03, 0.74, R(24), R(156), 0.0012, 0.0015, nu=34, nv=30, domeh=0.0016)   # one sculpted, domed back plate
shell2(0.77, 0.99, R(30), R(150), 0.0015, 0.0014, nu=14, nv=26, domeh=0.0008)   # smaller knuckle plate
# large blue disc on the back of the hand (reference): gold rim, dark bezel, glowing core
_c, _hw, _ht = palm_sec(0.36); _s = palm_axis(0.36); _s, _xa, _ya = frame_xy(_s, XW)
if _ya.dot(DD) < 0: _ya = -_ya
DISC_P = palm_ring(0.36, 0.0012 + 0.0016 + 0.0012, n=1, a0=R(90), a1=R(90), closed=False)[0]; DISC_N = _ya
HAND.add_bm(bm_cyl(0.0068, 0.0018, 48, bev=0.0005), frame(DISC_P, DISC_N, _s), 2)
HAND.add_bm(bm_cyl(0.0056, 0.0008, 48), frame(DISC_P + DISC_N * 0.0009, DISC_N, _s), 1)
HAND.add_bm(bm_torus(0.0044, NRAD / HK, 48, 8), frame(DISC_P + DISC_N * 0.0013, DISC_N, _s), 3)   # same line width after the HK scale
HAND.add_bm(bm_cyl(0.0030, 0.0010, 40, bev=0.0003), frame(DISC_P + DISC_N * 0.0012, DISC_N, _s), 3)
shell2(0.24, 0.84, R(214), R(300), 0.0010, 0.0012)           # palm pad (pinky side)
shell2(0.10, 0.55, R(300), R(338), 0.0010, 0.0012)           # thenar pad

# ---- wrist joint: ONE compact ribbed bearing between the forearm plates and the palm (no diameter step)
a_, u_, lat_, fr_, L_ = seg(1)
NJ = 48; J0 = E + u2 * (WJ0 - 0.0010)
r0 = []
for k in range(NJ):
    th = 2 * math.pi * k / NJ; A, d, r = radial(1, WJ0 - 0.0010, th); r0.append((d, r))
rr = np.array([r for _, r in r0]); rr = fill_nan(rr)
for _ in range(3): rr = (np.roll(rr, 1) + 2 * rr + np.roll(rr, -1)) / 4
P0r = [J0 + d * (rr[k] - 0.0016) for k, (d, _) in enumerate(r0)]
C1, hw1, ht1 = palm_sec(0.0); s1 = palm_axis(0.0); s1, Xa1, Ya1 = frame_xy(s1, XW)
if Ya1.dot(DD) < 0: Ya1 = -Ya1
P1r = []
for k, (d, _) in enumerate(r0):
    dd = d - s1 * d.dot(s1); a = math.atan2(dd.dot(Ya1), dd.dot(Xa1))
    q_ = ring_pts_se(C1, Xa1, Ya1, hw1 - 0.0004, ht1 - 0.0004, 2.2, 1, a, a, closed=False)[0]
    P1r.append(C1 + (q_ - C1) * HK)
NR = 36; jrows = []
for i in range(NR + 1):
    f = i / NR; fs = f * f * (3 - 2 * f)
    pts = [P0r[k].lerp(P1r[k], fs) for k in range(NJ)]
    c = sum(pts, V()) / NJ
    rib = 0.0
    if 0.12 < f < 0.90:
        q = (f - 0.12) / 0.78; rib = 0.5 + 0.5 * math.cos(2 * math.pi * 3 * q)
    m = 1.0 - 0.07 * math.sin(math.pi * f) + 0.035 * rib * math.sin(math.pi * f)
    jrows.append([c + (p - c) * m for p in pts])
JOINT = Acc("Robo_WristJoint", [M_GUN]); JOINT.add_bm(loft_bm(jrows), Matrix(), 0)
# thin gold seam where the joint meets the palm, steel bearing ring in the middle
for f_, rad, mi in ((0.985, 0.0007, 2),):
    i = int(f_ * NR); pts = jrows[i]; c = sum(pts, V()) / NJ
    pts = [c + (p - c) * 1.0 for p in pts]
    tube_obj("Robo_WristSeam_%d" % mi, [p + (p - c).normalized() * 0.0004 for p in pts], rad, M_GOLD if mi == 2 else M_STEEL, closed=True)

# ---- fingers: slim, tapering, anatomical phalanges, dorsal plates, dark joints
TIPS = {}
def rot(v, ax, deg): return (Matrix.Rotation(math.radians(deg), 3, ax) @ v).normalized()
def phalanx(a, b, s, ax, w0, w1, last):
    dors = s.cross(ax).normalized()
    L = (b - a).length
    jr = w0 * 0.31
    # dark joint: axle + rounded knuckle
    HAND.add_bm(bm_cyl(jr * 0.92, w0 * 0.84, 20, bev=0.0004), frame(a, ax, s), 5)
    HAND.add_bm(bm_sphere(jr * 0.95, 16, 10), Matrix.Translation(a), 1)
    # gunmetal inner link (palm side visible)
    HAND.add_bm(loft_bm([ring_pts_se(a.lerp(b, f) - dors * w0 * 0.06, ax, dors, w0 * 0.30, w0 * 0.27, 2.0, 14) for f in (0.0, 1.0)]), Matrix(), 1)
    # ivory dorsal cover: tapered, rounded ends; distal one closes over the tip
    g0 = jr * 0.70; g1 = (jr * 0.45) if not last else -w1 * 0.05
    NS = 12; rows = []
    for i in range(NS + 1):
        f = i / NS; t = g0 + (L - g0 - g1) * f
        e0 = min(1.0, f / 0.12); e1 = min(1.0, (1 - f) / (0.12 if not last else 0.35))
        cap = math.sqrt(max(0.02, min(e0, e1))) if not last else math.sqrt(max(0.02, min(e0, e1)))
        cap = 0.35 + 0.65 * cap
        hw = (w0 + (w1 - w0) * f) * 0.5 * cap; ht = (w0 + (w1 - w0) * f) * 0.36 * cap
        rows.append(ring_pts_se(a + s * t + dors * w0 * 0.10, ax, dors, hw, ht, 2.6, 20, vflat=0.75))
    HAND.add_bm(loft_bm(rows), Matrix(), 0)
    # small blue knuckle dot on the back of the joint (~40% of v2 size)
    pass   # v5: knuckle dots removed

def finger(name, base, s0, toward, lens, flex, w, wt=0.80):
    ax = s0.cross(toward).normalized()
    s = s0.copy(); p = base.copy(); joints = [p]; dirs = []
    for i in range(3):
        s = rot(s, ax, flex[i]); dirs.append(s)
    for L, s in zip(lens, dirs):
        p = p + s * L; joints.append(p)
    tot = sum(lens); acc = 0.0
    for i in range(3):
        w0 = w * (1 - (1 - wt) * acc / tot); acc += lens[i]; w1 = w * (1 - (1 - wt) * acc / tot)
        phalanx(joints[i], joints[i + 1], dirs[i], ax, w0, w1, i == 2)
    TIPS[name] = joints[-1]
    return joints

CK, hwK, htK = palm_sec(1.0); sK = palm_axis(1.0)
FING = [  # name, offset across the knuckle line (fraction of half width), z shift, spread, lengths (prox>mid>dist), flex, width
    ("Index", -0.72, 0.0010, -6.0, (0.0240, 0.0145, 0.0102), (10, 22, 14), 0.0088),
    ("Middle", -0.25, -0.0012, -1.5, (0.0268, 0.0160, 0.0110), (13, 27, 16), 0.0091),
    ("Ring", 0.25, -0.0002, 3.5, (0.0252, 0.0150, 0.0105), (16, 31, 18), 0.0086),
    ("Pinky", 0.70, 0.0030, 9.0, (0.0200, 0.0118, 0.0092), (20, 35, 20), 0.0074),
]
sK, XK, YK = frame_xy(sK, XW)
if YK.dot(DD) < 0: YK = -YK
for nm, fw, dz, spr, lens, flex, w in FING:
    base = CK + XK * (fw * hwK) + YK * (htK * 0.15) + sK * (-0.0030 - dz)
    s0 = rot(sK, YK, -spr)      # spread around the dorsal axis (index toward -w, pinky toward +w)
    if s0.dot(XK) * spr < 0: s0 = rot(sK, YK, spr)
    finger(nm, base, s0, -YK, lens, flex, w)
    # MCP glow dot on the knuckle plate
    # v5: MCP dots removed
# thumb: from the palm side (thenar), index edge, at a natural down/forward angle, curling toward the fingers
Cb, hwb, htb = palm_sec(0.30); sb = palm_axis(0.30); sb, Xb, Yb = frame_xy(sb, XW)
if Yb.dot(DD) < 0: Yb = -Yb
tb = Cb - Xb * (hwb * 0.82) - Yb * (htb * 0.45)
HAND.add_bm(bm_sphere(0.0050, 18, 12), Matrix.Translation(tb), 1)
ts0 = (sb * 0.86 - Xb * 0.30 - Yb * 0.36).normalized()
finger("Thumb", tb, ts0, (Xb * 0.45 - Yb * 0.55).normalized(), (0.0190, 0.0160, 0.0130), (6, 12, 14), 0.0098, 0.82)
log("hand done; tips", {k: tuple(round(c, 3) for c in v) for k, v in TIPS.items()})

HAND.V = [tuple(C1 + (V(p) - C1) * HK) for p in HAND.V]
TIPS = {k: C1 + (v - C1) * HK for k, v in TIPS.items()}
log('scaled tips', {k: tuple(round(c, 3) for c in v) for k, v in TIPS.items()})
for acc in (MECH, EMITTER, HAND, JOINT):
    acc.build(40)

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
SCULPT["cyber"] = 5
# v5: world = site background #0f0f12 (after AgX: linear 0.0078/0.0098 renders as 15,15,18)
SC.world.node_tree.nodes["Background"].inputs[0].default_value = (0.0078, 0.0078, 0.0098, 1)
# compositor preview glare (if the file has one): softer
sys.path.insert(0, "/tmp/claude-0/-home-user-kardonov-site/cb30cd45-1b88-5b9b-b3ff-480343f6cfce/scratchpad/scripts/c5")
from glowcomp import setup_glow, add_aov
import os as _os
AMB = float(_os.environ.get("AMBER_AOV", "3.0"))
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
