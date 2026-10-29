# Build hero props: Hammer (HUMAN) and Chisel (AI) -> assets/asset_tools.blend
# run: blender -b --factory-startup -P tools_build.py
import bpy, bmesh, math, os
from mathutils import Vector as V, Matrix, Euler

S = "/tmp/claude-0/-home-user-kardonov-site/cb30cd45-1b88-5b9b-b3ff-480343f6cfce/scratchpad"
OUT = S + "/assets/asset_tools.blend"
CM = 0.01
D = bpy.data
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
cos, sin, rad = math.cos, math.sin, math.radians

# ------------------------------------------------------------------ collections
def coll(name):
    c = D.collections.new(name); sc.collection.children.link(c); return c
C_TOOLS = coll("Tools"); C_STUDIO = coll("Studio")

# ------------------------------------------------------------------ materials
def mat(name, base, metal=0.0, rough=0.4, coat=0.0, emis=None, estr=0.0, vp=None, rough_var=0.0, bump=0.0, bump_scale=600.0, aniso=0.0):
    m = D.materials.new(name); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*base, 1)
    b.inputs["Metallic"].default_value = metal
    b.inputs["Roughness"].default_value = rough
    b.inputs["Coat Weight"].default_value = coat
    b.inputs["Coat Roughness"].default_value = 0.2
    if aniso: b.inputs["Anisotropic"].default_value = aniso
    if emis:
        b.inputs["Emission Color"].default_value = (*emis, 1)
        b.inputs["Emission Strength"].default_value = estr
    if rough_var or bump:
        tc = nt.nodes.new("ShaderNodeTexCoord")
        nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = bump_scale
        nz.inputs["Detail"].default_value = 8.0; nz.inputs["Roughness"].default_value = 0.6
        nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
        if rough_var:
            mr = nt.nodes.new("ShaderNodeMapRange")
            mr.inputs["To Min"].default_value = rough - rough_var
            mr.inputs["To Max"].default_value = rough + rough_var
            nz2 = nt.nodes.new("ShaderNodeTexNoise"); nz2.inputs["Scale"].default_value = bump_scale * 0.08
            nz2.inputs["Detail"].default_value = 4.0
            nt.links.new(tc.outputs["Object"], nz2.inputs["Vector"])
            nt.links.new(nz2.outputs["Fac"], mr.inputs["Value"]); nt.links.new(mr.outputs["Result"], b.inputs["Roughness"])
        if bump:
            bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump
            bp.inputs["Distance"].default_value = 0.0004
            nt.links.new(nz.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    m.diffuse_color = (*(vp or base), 1)
    return m

M_GOLD = mat("Tool_Gold", (0.98, 0.62, 0.26), metal=1.0, rough=0.19, rough_var=0.04)
M_BRONZE = mat("Tool_Bronze", (1.0, 0.70, 0.38), metal=1.0, rough=0.14, rough_var=0.03, aniso=0.3)
M_LEATHER = mat("Tool_Leather", (0.56, 0.40, 0.25), rough=0.58, coat=0.1, bump=0.25, bump_scale=900.0, rough_var=0.06)
M_AMBER = mat("Tool_GlowAmber", (1.0, 0.40, 0.05), rough=0.3, emis=(1.0, 0.40, 0.04), estr=5.0, vp=(1.0, 0.6, 0.2))
M_GUN = mat("Tool_Gunmetal", (0.36, 0.40, 0.47), metal=1.0, rough=0.26, aniso=0.35, rough_var=0.06, bump=0.04, bump_scale=1500.0)
M_GUNDARK = mat("Tool_GunmetalDark", (0.035, 0.04, 0.05), metal=0.8, rough=0.45)
M_STEEL = mat("Tool_Steel", (0.96, 0.97, 1.0), metal=0.8, rough=0.16, coat=0.6, aniso=0.3)
M_BLUE = mat("Tool_GlowBlue", (0.02, 0.25, 0.9), rough=0.3, emis=(0.01, 0.30, 1.0), estr=5.0, vp=(0.25, 0.66, 1.0))
M_BLUE_RING = mat("Tool_GlowBlueRing", (0.0, 0.0, 0.0), rough=0.35, emis=(0.01, 0.30, 1.0), estr=2.2, vp=(0.25, 0.66, 1.0))  # same hue, lower strength: wide rings stay saturated #3fa9ff

# marble from the statue file (copied into this file; source untouched)
with D.libraries.load(S + "/assets/asset_statue.blend", link=False) as (src, dst):
    dst.materials = ["Marble"]
M_MARBLE = D.materials["Marble"]

# ------------------------------------------------------------------ helpers
def empty(name, loc=(0, 0, 0), parent=None, col=C_TOOLS, size=0.05):
    e = D.objects.new(name, None); e.empty_display_size = size; e.location = loc
    col.objects.link(e)
    if parent: e.parent = parent
    return e

class MB:
    def __init__(s, name, mats):
        s.name, s.mats = name, mats; s.V = []; s.F = []; s.M = []
    def v(s, p): s.V.append(tuple(p)); return len(s.V) - 1
    def face(s, ids, m=0): s.F.append(list(ids)); s.M.append(m)
    def loft(s, rings, mat_fn, closed=True, cap0=None, cap1=None):
        ids = [[s.v(p) for p in r] for r in rings]; n = len(rings[0])
        for i in range(len(rings) - 1):
            for j in range(n if closed else n - 1):
                m = mat_fn(i, j)
                if m is None: continue
                j2 = (j + 1) % n
                s.face([ids[i][j], ids[i][j2], ids[i + 1][j2], ids[i + 1][j]], m)
        if cap0 is not None: s.face(list(reversed(ids[0])), cap0)
        if cap1 is not None: s.face(ids[-1], cap1)
        return ids
    def build(s, parent, sharp=35, bevel=0.0, seg=3, angle=30, props=None, weld=True):
        me = D.meshes.new(s.name)
        me.from_pydata([(x * CM, y * CM, z * CM) for x, y, z in s.V], [], s.F)
        for m in s.mats: me.materials.append(m)
        me.polygons.foreach_set("material_index", s.M); me.update()
        bm = bmesh.new(); bm.from_mesh(me)
        if weld: bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=2e-6)
        bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-7)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(me); bm.free()
        me.shade_smooth()
        try: me.set_sharp_from_angle(angle=rad(sharp))
        except Exception as ex: print("sharp fail", ex)
        ob = D.objects.new(s.name, me); C_TOOLS.objects.link(ob); ob.parent = parent
        if bevel:
            bv = ob.modifiers.new("Bevel", "BEVEL"); bv.width = bevel * CM; bv.segments = seg
            bv.limit_method = 'ANGLE'; bv.angle_limit = rad(angle); bv.harden_normals = True
            bv.use_clamp_overlap = True; bv.miter_outer = 'MITER_ARC'
        for k, v in (props or {}).items(): ob[k] = v
        return ob

def lathe(mb, prof, segs=64, mats=None, center=(0, 0), cap_top=None, cap_bot=None, phase=0.0):
    """prof: list of (r, z) top->bottom or any order; mats: per band index (len(prof)-1) or int"""
    rings = []
    for r, z in prof:
        rings.append([(center[0] + r * cos(2 * math.pi * j / segs + phase), center[1] + r * sin(2 * math.pi * j / segs + phase), z) for j in range(segs)])
    mf = (lambda i, j: mats[i]) if isinstance(mats, (list, tuple)) else (lambda i, j: mats or 0)
    return mb.loft(rings, mf, cap0=cap_top, cap1=cap_bot)

def torus(mb, R, r, z, mi=0, seg=64, rseg=12, center=(0, 0)):
    rings = []
    for i in range(rseg):
        a = 2 * math.pi * i / rseg
        rr, zz = R + r * cos(a), z + r * sin(a)
        rings.append([(center[0] + rr * cos(2 * math.pi * j / seg), center[1] + rr * sin(2 * math.pi * j / seg), zz) for j in range(seg)])
    rings.append(rings[0])
    mb.loft(rings, lambda i, j: mi)

# =========================================================================================
#                                    HAMMER  (HUMAN)
# =========================================================================================
HAM = empty("Hammer", loc=(-0.12, 0, 0), size=0.1)
HZ = 29.5           # head centre height (cm), head axis = X
A0 = 2.45           # head half size (apothem of chamfered square)
YOKE = 1.32         # half width of the central gold yoke
BLK = 4.3           # marble block end
HP = {"polish": 1.0, "gold": 0.0}

def octo(a, c):      # chamfered square in (u,v); faces: even=flat, odd=chamfer
    d = a - c
    return [(a, -d), (a, d), (d, a), (-d, a), (-a, d), (-a, -d), (-d, -a), (d, -a)]

def head_ring(x, a, cr=0.31):
    return [(x, u, HZ + v) for u, v in octo(a, a * cr)]

# --- marble blocks (both sides): flats marble, chamfers gold
mb = MB("Hammer_Marble", [M_MARBLE, M_GOLD])
for sgn in (1, -1):
    mb.loft([head_ring(sgn * (YOKE - 0.1), A0), head_ring(sgn * (BLK + 0.05), A0)], lambda i, j: 0 if j % 2 == 0 else 1)
mb.build(HAM, sharp=30, bevel=0.035, seg=2, props=HP)

# --- gold frames around each marble panel (4 faces x 2 blocks)
def rrect(L, W, r, n=6):
    pts = []
    for cx, cy, a0 in ((L - r, W - r, 0), (-(L - r), W - r, 90), (-(L - r), -(W - r), 180), (L - r, -(W - r), 270)):
        for k in range(n + 1):
            a = rad(a0 + 90 * k / n); pts.append((cx + r * cos(a), cy + r * sin(a)))
    return pts

mb = MB("Hammer_Frames", [M_GOLD])
flat_half = A0 - A0 * 0.31          # half width of flat face
for sgn in (1, -1):
    xc = sgn * (YOKE + BLK) / 2; L = (BLK - YOKE) / 2 - 0.02
    W = flat_half + 0.02; b = 0.16; h = 0.08
    for k in range(4):                   # face normals: +y, +z, -y, -z
        ang = rad(90 * k); n = V((0, cos(ang), sin(ang))); t2 = V((0, -sin(ang), cos(ang))); t1 = V((1, 0, 0))
        base = V((xc, 0, HZ)) + n * A0
        def loop(LL, WW, rr, off):
            return [tuple(base + t1 * p[0] + t2 * p[1] + n * off) for p in rrect(LL, WW, rr)]
        rings = [loop(L, W, 0.30, -0.06), loop(L, W, 0.30, h), loop(L - b, W - b, 0.12, h), loop(L - b, W - b, 0.12, -0.06)]
        mb.loft(rings + [rings[0]], lambda i, j: 0)
mb.build(HAM, sharp=40, bevel=0.025, seg=2)

# --- central yoke (gold) with two fine grooves
mb = MB("Hammer_Yoke", [M_GOLD, M_BRONZE])
ay = A0 + 0.14
spec = [(-YOKE, A0 - 0.05), (-YOKE, ay), (-YOKE + 0.25, ay), (-YOKE + 0.25, ay - 0.06), (-YOKE + 0.38, ay - 0.06), (-YOKE + 0.38, ay),
        (YOKE - 0.38, ay), (YOKE - 0.38, ay - 0.06), (YOKE - 0.25, ay - 0.06), (YOKE - 0.25, ay), (YOKE, ay), (YOKE, A0 - 0.05)]
mb.loft([head_ring(x, a) for x, a in spec], lambda i, j: 1 if i in (3, 7) else 0)
mb.build(HAM, sharp=30, bevel=0.03, seg=3)

# --- end bands + striking faces (both ends)
mb = MB("Hammer_Ends", [M_GOLD, M_BRONZE])
ab = A0 + 0.16
for sgn in (1, -1):
    X = lambda x: sgn * x
    spec = [(BLK - 0.05, A0 - 0.05, 0), (BLK, ab, 0), (BLK + 0.30, ab, 0), (BLK + 0.30, ab - 0.07, 1), (BLK + 0.42, ab - 0.07, 0),
            (BLK + 0.42, ab, 0), (BLK + 0.95, ab, 0), (BLK + 0.95, A0 + 0.02, 0), (BLK + 1.55, A0 - 0.30, 0),
            (BLK + 1.62, A0 - 0.42, 0), (BLK + 1.62, A0 - 0.62, 1), (BLK + 1.66, A0 - 0.85, 1),
            (BLK + 1.71, A0 - 1.5, 1), (BLK + 1.73, 0.02, 1)]
    rings = [head_ring(X(x), a, 0.31 if a > 1.0 else 0.31) for x, a, _ in spec]
    mb.loft(rings, lambda i, j, spec=spec: spec[i][2] if i < len(spec) - 1 else 1, cap1=1)
mb.build(HAM, sharp=30, bevel=0.03, seg=3)

# --- top medallion (echo of the headband medallion) with amber ring
top = HZ + ay
mb = MB("Hammer_Medallion", [M_GOLD, M_BRONZE])
lathe(mb, [(0.80, top - 0.05), (0.80, top + 0.10), (0.74, top + 0.18), (0.62, top + 0.20), (0.62, top + 0.12),
           (0.42, top + 0.12), (0.42, top + 0.22), (0.30, top + 0.29), (0.0, top + 0.31)], segs=64,
      mats=[0, 0, 0, 0, 1, 0, 0, 0])
mb.build(HAM, sharp=40, bevel=0.02, seg=2)
mb = MB("Hammer_GlowTop", [M_AMBER]); torus(mb, 0.52, 0.055, top + 0.14, seg=64, rseg=10); mb.build(HAM, sharp=80)
# same medallion on both yoke sides (+Y / -Y), facing out
for sgn in (1, -1):
    for nm, src in (("Hammer_MedallionSide", "Hammer_Medallion"), ("Hammer_GlowSide", "Hammer_GlowTop")):
        o = D.objects[src].copy(); o.data = D.objects[src].data.copy(); o.name = nm + ("_P" if sgn > 0 else "_N")
        C_TOOLS.objects.link(o); o.parent = HAM
        pivot = V((0, 0, HZ * CM))
        M = Matrix.Translation(pivot) @ Matrix.Rotation(rad(-90 * sgn), 4, 'X') @ Matrix.Translation(-pivot)
        o.data.transform(M); o.data.update()

# --- handle socket collar with amber spark ring
bot = HZ - ay
mb = MB("Hammer_Collar", [M_GOLD, M_BRONZE])
lathe(mb, [(1.22, bot + 0.3), (1.22, bot - 0.10), (1.34, bot - 0.16), (1.34, bot - 0.26), (1.20, bot - 0.32), (1.20, bot - 0.54),
           (1.34, bot - 0.60), (1.34, bot - 0.72), (1.12, bot - 1.70), (1.08, bot - 2.05), (1.18, bot - 2.12), (1.18, bot - 2.34),
           (1.06, bot - 2.42), (1.0, bot - 2.5)], segs=72, mats=[0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0])
mb.build(HAM, sharp=35, bevel=0.025, seg=2)
mb = MB("Hammer_GlowSpark", [M_AMBER]); torus(mb, 1.25, 0.09, bot - 0.43, seg=72, rseg=12); mb.build(HAM, sharp=80)
SHAFT_TOP = bot - 2.4

# --- upper shaft (marble)
mb = MB("Hammer_Shaft", [M_MARBLE])
lathe(mb, [(1.02, SHAFT_TOP + 0.1), (1.04, SHAFT_TOP - 3.0), (1.10, 18.0), (1.13, 16.5)], segs=64)
mb.build(HAM, sharp=60, props=HP)

# --- mid collar
mb = MB("Hammer_MidCollar", [M_GOLD, M_BRONZE])
lathe(mb, [(1.08, 16.95), (1.22, 16.88), (1.32, 16.74), (1.32, 16.52), (1.24, 16.45), (1.24, 16.25), (1.36, 16.18),
           (1.52, 15.98), (1.52, 15.72), (1.40, 15.62), (1.25, 15.55)], segs=72, mats=[0, 0, 0, 0, 1, 0, 0, 0, 0, 0])
mb.build(HAM, sharp=35, bevel=0.02, seg=2)

# --- leather / cord grip, helical overlapping strap
G0, G1, PITCH, NT = 2.95, 15.75, 1.18, 96
mb = MB("Hammer_Grip", [M_LEATHER])
def strap(u):
    if u < 0.86: return 0.25 + 0.75 * math.sin(0.5 * math.pi * (u / 0.86)) ** 0.8
    t = (u - 0.86) / 0.14; return 0.25 + 0.75 * cos(0.5 * math.pi * t) ** 1.5
rings = []
nz = int((G1 - G0) / 0.035)
for i in range(nz + 1):
    z = G0 + (G1 - G0) * i / nz; ring = []
    for j in range(NT):
        th = 2 * math.pi * j / NT
        u = (z / PITCH - j / NT) % 1.0
        r = 1.30 + 0.12 * strap(u)
        ring.append((r * cos(th), r * sin(th), z))
    rings.append(ring)
mb.loft(rings, lambda i, j: 0)
mb.build(HAM, sharp=180)

# --- lower collar + pommel
mb = MB("Hammer_Pommel", [M_GOLD, M_BRONZE, M_AMBER])
lathe(mb, [(1.25, 3.25), (1.42, 3.18), (1.52, 3.02), (1.52, 2.80), (1.40, 2.72), (1.40, 2.52), (1.54, 2.44), (1.54, 2.22),
           (1.36, 2.10), (1.34, 1.98), (1.58, 1.78), (1.80, 1.35), (1.84, 0.95), (1.76, 0.55), (1.58, 0.22), (1.32, 0.04),
           (0.95, 0.0), (0.82, 0.07), (0.60, 0.07), (0.0, 0.02)], segs=72,
      mats=[0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1])
mb.build(HAM, sharp=35, bevel=0.02, seg=2)

# marble space for the hammer (moves with the hammer, finer veins at prop scale)
MS = empty("MarbleSpace_Tools", loc=(0, 0, HZ * CM), parent=HAM, size=0.03)
MS.rotation_euler = (0.35, 0.6, 0.25); MS.scale = (0.2, 0.2, 0.2)
for n in M_MARBLE.node_tree.nodes:
    if n.type == 'TEX_COORD': n.object = MS
for o in HAM.children: o["polish"] = 1.0; o["gold"] = 0.0

# =========================================================================================
#                                    CHISEL  (AI)
# =========================================================================================
CHI = empty("Chisel", loc=(0.12, 0, 0), size=0.1)
T8 = math.tan(math.pi / 8)

def oct_ring(z, R, sx=1.0, sy=1.0, de=0.0, do=0.0, we=0.095, wo=0.11):
    """octagon (apothem R) with a notch (groove) in each face; 5 verts per face:
    corner, groove-start, groove-start-in, groove-end-in, groove-end"""
    rc = R / cos(math.pi / 8); pts = []
    for k in range(8):
        a0 = rad(-22.5 + 45 * k); a1 = a0 + rad(45)
        c0 = V((rc * cos(a0), rc * sin(a0))); c1 = V((rc * cos(a1), rc * sin(a1)))
        n = V((cos(rad(45 * k)), sin(rad(45 * k)))); t = (c1 - c0).normalized(); mid = (c0 + c1) / 2
        d, w = (de, we) if k % 2 == 0 else (do, wo)
        w = min(w, R * T8 * 0.8)
        for p in (c0, mid - t * w, mid - t * w - n * d, mid + t * w - n * d, mid + t * w):
            pts.append((p.x * sx, p.y * sy, z))
    return pts

# ring spec: (z, R, sx, sy, de, do, band_material_to_next)
G, GUN, GD, ST, BL = 0, 1, 2, 3, 4
spec = [
    (0.00, 0.93, 1.22, 0.012, 0, 0, BL),
    (0.05, 0.93, 1.22, 0.024, 0, 0, ST),
    (1.88, 0.93, 1.16, 0.32, 0, 0, G),
    (2.06, 0.93, 1.16, 0.335, 0, 0, GUN),
    (6.30, 0.93, 1.0, 1.0, 0, 0, GUN),
    (6.30, 1.00, 1.0, 1.0, 0, 0, G),
    (6.80, 1.00, 1.0, 1.0, 0, 0, G),
    (6.80, 0.935, 1.0, 1.0, 0, 0, GUN),
    (7.35, 0.94, 1.0, 1.0, 0, 0, GUN),
    (7.50, 0.942, 1.0, 1.0, 0.085, 0, GUN),
    (19.00, 1.0, 1.0, 1.0, 0.085, 0, GUN),
    (19.15, 1.0, 1.0, 1.0, 0, 0, GUN),
    (19.70, 1.0, 1.0, 1.0, 0, 0, GUN),
    (20.30, 1.20, 1.0, 1.0, 0, 0, GUN),
    (20.30, 1.42, 1.0, 1.0, 0, 0, G),
    (20.42, 1.44, 1.0, 1.0, 0, 0, G),
    (20.70, 1.44, 1.0, 1.0, 0, 0, G),
    (20.80, 1.40, 1.0, 1.0, 0, 0, G),
    (20.80, 1.32, 1.0, 1.0, 0, 0, GUN),
    (21.25, 1.32, 1.0, 1.0, 0, 0, GUN),
    (21.40, 1.32, 1.0, 1.0, 0, 0.08, GUN),
    (23.00, 1.32, 1.0, 1.0, 0, 0.08, GUN),
    (23.15, 1.32, 1.0, 1.0, 0, 0, GUN),
    (23.60, 1.32, 1.0, 1.0, 0, 0, GUN),
    (23.98, 1.06, 1.0, 1.0, 0, 0, GUN),
    (23.98, 0.80, 1.0, 1.0, 0, 0, GD),
    (23.92, 0.80, 1.0, 1.0, 0, 0, BL),
    (23.92, 0.68, 1.0, 1.0, 0, 0, GD),
    (23.98, 0.68, 1.0, 1.0, 0, 0, GUN),
    (24.02, 0.30, 1.0, 1.0, 0, 0, GUN),
    (24.03, 0.02, 1.0, 1.0, 0, 0, GUN),
]
BR = 5
spec = [r[:6] + (BR if r[6] == G else r[6],) for r in spec]   # chisel = pure AI: former gold rings become blue neon
rings = [oct_ring(z, R, sx, sy, de, do) for z, R, sx, sy, de, do, _ in spec]
def cmat(i, j):
    m = spec[i][6]; q = j % 5; k = j // 5
    if m in (GUN,) and q in (1, 2, 3):
        dk = (spec[i][4], spec[i + 1][4]) if k % 2 == 0 else (spec[i][5], spec[i + 1][5])
        if dk[0] > 0 and dk[1] > 0: return BL if q == 2 else GD
        if (dk[0] > 0 or dk[1] > 0) and q == 2: return GD
        if (dk[0] > 0 or dk[1] > 0): return GD
    return m
mb = MB("Chisel_Body", [M_GOLD, M_GUN, M_GUNDARK, M_STEEL, M_BLUE, M_BLUE_RING])
mb.loft(rings, cmat, cap0=BL, cap1=GUN)
mb.build(CHI, sharp=28, bevel=0.03, seg=3, angle=25)

# ------------------------------------------------------------------ studio
def area(name, loc, energy, color, size, target=(0, 0, 0.16)):
    L = D.lights.new(name, 'AREA'); L.energy = energy; L.color = color; L.size = size
    o = D.objects.new(name, L); C_STUDIO.objects.link(o); o.location = loc
    o.rotation_euler = (V(target) - V(loc)).to_track_quat('-Z', 'Y').to_euler()
    return o
area("Key", (0.55, -0.65, 0.75), 24.0, (1.0, 0.88, 0.76), 0.45)
area("Fill", (-0.85, -0.45, 0.35), 8.0, (0.85, 0.88, 1.0), 0.9)
area("Rim", (-0.25, 0.75, 0.65), 32.0, (1.0, 0.82, 0.62), 0.35)
area("Top", (0.0, 0.0, 1.0), 5.0, (1.0, 0.95, 0.9), 1.2)
area("RimCool", (0.7, 0.6, 0.45), 30.0, (0.75, 0.85, 1.0), 0.3)
cam_d = D.cameras.new("Camera"); cam = D.objects.new("Camera", cam_d); C_STUDIO.objects.link(cam); sc.camera = cam
cam_d.lens = 85; cam_d.clip_start = 0.01

w = D.worlds.new("ToolsWorld"); sc.world = w; w.use_nodes = True
# studio environment for reflections: dark floor, soft warm ceiling, two vertical strip softboxes
wn = w.node_tree; bg = wn.nodes["Background"]; bg.inputs["Strength"].default_value = 1.0
tc = wn.nodes.new("ShaderNodeTexCoord"); sep = wn.nodes.new("ShaderNodeSeparateXYZ"); wn.links.new(tc.outputs["Generated"], sep.inputs[0])
def ramp(inp, stops):
    r = wn.nodes.new("ShaderNodeValToRGB"); el = r.color_ramp.elements
    el[0].position, el[0].color = stops[0][0], (*stops[0][1], 1); el[1].position, el[1].color = stops[1][0], (*stops[1][1], 1)
    for pos, col in stops[2:]:
        e = el.new(pos); e.color = (*col, 1)
    wn.links.new(inp, r.inputs[0]); return r
rz = ramp(sep.outputs["Z"], [(0.0, (0.06, 0.055, 0.05)), (0.45, (0.10, 0.09, 0.08)), (0.52, (0.30, 0.27, 0.24)), (0.62, (0.08, 0.07, 0.065)), (0.85, (0.35, 0.31, 0.27)), (1.0, (0.7, 0.62, 0.54))])
rx = ramp(sep.outputs["X"], [(0.0, (0, 0, 0)), (0.06, (2.2, 2.1, 2.0)), (0.14, (0, 0, 0)), (0.86, (0, 0, 0)), (0.93, (1.6, 1.4, 1.2)), (1.0, (0, 0, 0))])
add = wn.nodes.new("ShaderNodeMix"); add.data_type = 'RGBA'; add.blend_type = 'ADD'; add.inputs["Factor"].default_value = 1.0
wn.links.new(rz.outputs["Color"], add.inputs[6]); wn.links.new(rx.outputs["Color"], add.inputs[7]); wn.links.new(add.outputs[2], bg.inputs["Color"])
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'None'
sc.render.engine = 'BLENDER_EEVEE_NEXT'; sc.eevee.taa_render_samples = 24
sc.render.film_transparent = True
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'

os.makedirs(os.path.dirname(OUT), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("SAVED", OUT, len(D.objects), "objects")
