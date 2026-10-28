# Stage 2: build the robotic arm (from the cut-away marble arm "ArmRef") and the neural headband.
# Run on out/cyber/stage_cut.blend (made by cyber_cut.py):  blender -b stage_cut.blend -P cyber_build.py -- OUT.blend
import bpy, bmesh, sys, math, time
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index("--") + 1:]
OUT = argv[0]
T0 = time.time()
def log(*a): print("[cyber %.1fs]" % (time.time() - T0), *a, flush=True)

D = bpy.data
SC = bpy.context.scene
SCULPT = D.objects["Sculpture_HiRes"]
ARMREF = D.objects["ArmRef"]
V = Vector

# ---------------------------------------------------------------- skeleton (measured on the mesh)
P0 = V((-0.108, 0, 0.70)); NCUT = V((-0.994, 0, 0.108)).normalized()   # shoulder cut plane (outer = +)
S = V((-0.128, 0.032, 0.765))     # shoulder joint
E = V((-0.151, 0.046, 0.625))     # elbow
W = V((-0.175, -0.002, 0.502))    # wrist
H = V((-0.180, -0.006, 0.455))    # knuckle line centre
u1 = (E - S).normalized(); u2 = (W - E).normalized(); u3 = (H - W).normalized()

# ---------------------------------------------------------------- materials
def mat_principled(name, base, metal=0.0, rough=0.4, coat=0.0, emis=None, estr=0.0, spec=0.5):
    m = D.materials.get(name) or D.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree; b = nt.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*base, 1)
    b.inputs["Metallic"].default_value = metal
    b.inputs["Roughness"].default_value = rough
    b.inputs["Coat Weight"].default_value = coat
    b.inputs["Coat Roughness"].default_value = 0.15
    b.inputs["Specular IOR Level"].default_value = spec
    if emis:
        b.inputs["Emission Color"].default_value = (*emis, 1)
        b.inputs["Emission Strength"].default_value = estr
    m.diffuse_color = (*base, 1)
    return m

M_IVORY = mat_principled("Cyber_Ivory", (0.68, 0.60, 0.47), rough=0.28, coat=0.6)
M_GOLD = mat_principled("Cyber_Gold", (0.95, 0.70, 0.36), metal=1.0, rough=0.34)
M_GUN = mat_principled("Cyber_Gunmetal", (0.055, 0.058, 0.065), metal=0.9, rough=0.32)
M_BLUE = mat_principled("Cyber_GlowBlue", (0.02, 0.25, 1.0), rough=0.3, emis=(0.02, 0.26, 1.0), estr=5.0)
M_AMBER_GOLD = mat_principled("Neuro_Gold", (1.0, 0.68, 0.32), metal=1.0, rough=0.32)
M_AMBER = mat_principled("Neuro_GlowAmber", (1.0, 0.55, 0.15), rough=0.3, emis=(1.0, 0.36, 0.04), estr=4.5)
M_LENS = mat_principled("Neuro_Lens", (0.9, 0.75, 0.5), metal=0.6, rough=0.15, emis=(1.0, 0.62, 0.25), estr=3.0)
M_BLUE.diffuse_color = (0.25, 0.66, 1.0, 1); M_AMBER.diffuse_color = (1.0, 0.6, 0.2, 1)

# ---------------------------------------------------------------- helpers
def new_obj(name, me, mats=(), parent=SCULPT):
    ob = D.objects.new(name, me); SC.collection.objects.link(ob)
    for m in mats: me.materials.append(m)
    ob.parent = parent; ob.matrix_parent_inverse = parent.matrix_world.inverted()
    return ob

def apply_mods(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    old = ob.data; ob.modifiers.clear(); ob.data = me; D.meshes.remove(old)

def bm_from(ob):
    bm = bmesh.new(); bm.from_mesh(ob.data); return bm

def smooth_shade(me):
    me.polygons.foreach_set("use_smooth", [True] * len(me.polygons)); me.update()

def poly_tube(name, pts, radius, mat, closed=False, res=6, parent=SCULPT):
    cu = D.curves.new(name, 'CURVE'); cu.dimensions = '3D'
    sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1)
    for p, q in zip(sp.points, pts): p.co = (*q, 1)
    sp.use_cyclic_u = closed
    cu.bevel_depth = radius; cu.bevel_resolution = res // 2; cu.use_fill_caps = True
    ob = D.objects.new(name, cu); SC.collection.objects.link(ob); cu.materials.append(mat)
    ob.parent = parent
    return ob

def smooth_pts(pts, it=3, closed=False):
    P = np.array([tuple(p) for p in pts])
    for _ in range(it):
        if closed: P = (np.roll(P, 1, 0) + 2 * P + np.roll(P, -1, 0)) / 4
        else: P[1:-1] = (P[:-2] + 2 * P[1:-1] + P[2:]) / 4
    return [V(p) for p in P]

def orient_to(ob, loc, normal):
    ob.location = loc
    ob.rotation_euler = V(normal).to_track_quat('Z', 'Y').to_euler()

# ---------------------------------------------------------------- 1. base arm mesh (closed, remeshed)
log("remesh arm")
bm = bm_from(ARMREF)
bnd = [e for e in bm.edges if e.is_boundary]
bmesh.ops.holes_fill(bm, edges=bnd, sides=0)
bm.to_mesh(ARMREF.data); bm.free()
mod = ARMREF.modifiers.new("rm", 'REMESH'); mod.mode = 'VOXEL'; mod.voxel_size = 0.0011
mod.use_smooth_shade = True
apply_mods(ARMREF)
log("remeshed faces", len(ARMREF.data.polygons))

def make_layer(name, offset, smooth_it, smooth_fac=0.5):
    me = ARMREF.data.copy(); ob = new_obj(name, me)
    if smooth_it:
        m = ob.modifiers.new("lap", 'LAPLACIANSMOOTH'); m.iterations = smooth_it; m.lambda_factor = smooth_fac
        m.use_volume_preserve = True; m.use_normalized = True
    m = ob.modifiers.new("disp", 'DISPLACE'); m.strength = offset; m.mid_level = 0.0; m.direction = 'NORMAL'
    apply_mods(ob)
    # open it at the cut plane (remove the cap part lying on the plane)
    bm = bm_from(ob)
    kill = [f for f in bm.faces if (f.calc_center_median() - P0).dot(NCUT) < 0.0012]
    bmesh.ops.delete(bm, geom=kill, context='FACES')
    bm.to_mesh(ob.data); bm.free(); smooth_shade(ob.data)
    return ob

CORE = make_layer("Robo_Core", -0.0010, 4, 0.4)
HANDW = None
CORE.data.materials.append(M_GUN)
SHELLBASE = make_layer("Robo_ShellBase", 0.0005, 12, 0.6)
log("layers done")

# ---------------------------------------------------------------- 2. plate segmentation
# A plane cut = (point, normal). Bands = gap regions between two parallel planes (dark core shows),
# bordered with thin gold strips. Wedges = longitudinal openings around a bone axis.
def sd(p, pt, n): return (p - pt).dot(n)

class Band:
    def __init__(s, pt, n, w, gold=0.0012, filt=None):
        s.pt, s.n, s.w, s.gold, s.filt = pt, n.normalized(), w, gold, filt or (lambda p: True)
    def planes(s):
        h = s.w / 2; g = s.gold
        return [(s.pt + s.n * o, s.n) for o in (-h - g, -h, h, h + g)]
    def classify(s, p):
        if not s.filt(p): return None
        d = abs(sd(p, s.pt, s.n))
        if d < s.w / 2: return 'gap'
        if d < s.w / 2 + s.gold: return 'gold'
        return None

class Wedge:   # opening around axis a->b, centred on direction 'c' (perp), half-angle 'ha' (deg)
    def __init__(s, a, b, c, ha, gold_deg=4.0, filt=None):
        s.a, s.ax = a, (b - a).normalized()
        c = (c - s.ax * c.dot(s.ax)).normalized(); s.c = c; s.c2 = s.ax.cross(c)
        s.ha, s.g = math.radians(ha), math.radians(gold_deg); s.filt = filt or (lambda p: True)
    def ang(s, p):
        q = p - s.a; return math.atan2(q.dot(s.c2), q.dot(s.c))
    def planes(s):
        out = []
        for a in (s.ha, -s.ha, s.ha + s.g, -s.ha - s.g):
            dirv = s.c * math.cos(a) + s.c2 * math.sin(a)
            out.append((s.a, s.ax.cross(dirv).normalized()))
        return out
    def classify(s, p):
        if not s.filt(p): return None
        a = abs(s.ang(p))
        if a < s.ha: return 'gap'
        if a < s.ha + s.g: return 'gold'
        return None

nEl = (u1 + u2).normalized(); nWr = (u2 + u3).normalized()
d_cut = lambda p: sd(p, P0, NCUT)
inUpper = lambda p: sd(p, S + u1 * 0.058, u1) > 0 and sd(p, E, nEl) < -0.006
inFore = lambda p: sd(p, E, nEl) > 0.006 and sd(p, W, nWr) < -0.003
inHand = lambda p: sd(p, W, nWr) > 0
inCurl = lambda p: p.z < 0.447 and inHand(p)
inner_dir = V((1, -0.15, 0))      # medial side (towards the body)
fore_front = V((0.2, -1, 0))      # front of the forearm (thumb side)

FEATS = [
    Band(P0 + NCUT * 0.0080, NCUT, 0.010, 0.0022, filt=lambda p: p.z > 0.6),       # shoulder socket ring
    Band(S + u1 * 0.058, u1, 0.0045, 0.0024, filt=lambda p: d_cut(p) > 0.016),     # pauldron / upper arm
    Band(E, nEl, 0.016, 0.0020),                                                     # elbow
    Band(W, nWr, 0.008, 0.0018),                                                     # wrist
    Band(H + u3 * 0.001, u3, 0.0028, 0.0008, filt=lambda p: inHand(p)),                 # MCP knuckles
    Band(V((0, 0, 0.437)), V((0, 0, 1)), 0.0024, 0.0, filt=lambda p: p.x < -0.168 and inHand(p) and p.z < 0.45),
    Band(V((-0.159, 0, 0)), V((1, 0, 0)), 0.0024, 0.0, filt=lambda p: inCurl(p) and p.x > -0.17),
    Wedge(S + u1 * 0.058, E, inner_dir, 38, filt=inUpper),                          # upper arm medial opening
    Wedge(E, W, inner_dir, 34, filt=inFore),                                        # forearm medial opening
    Wedge(E, W, fore_front, 8.0, gold_deg=3.0, filt=inFore),                        # forearm front seam (blue line)
    Wedge(S + u1 * 0.058, E, V((-0.3, -1, 0)), 8.0, gold_deg=3.0, filt=inUpper),    # upper arm front seam
    Wedge(S + u1 * 0.058, E, V((-0.5, 1, 0)), 14.0, gold_deg=3.5, filt=inUpper),     # upper arm back seam
    Wedge(E, W, V((-0.3, 1, 0)), 10.0, gold_deg=3.5, filt=inFore),                   # forearm back seam
    Band(E.lerp(W, 0.47), u2, 0.0012, 0.0, filt=inFore),                            # forearm panel line
    Band(S - u1 * 0.004, u1, 0.0016, 0.0012, filt=lambda p: d_cut(p) > 0.012 and p.z > 0.66),  # pauldron layer line
    Band(V((-0.138, 0, 0)), V((1, 0, 0)), 0.056, 0.0010, filt=lambda p: inHand(p) and sd(p, H + u3 * 0.001, u3) < -0.0014 and p.y > -0.022),  # dark palm
    Band(V((0, -0.0155, 0)), V((0, 1, 0)), 0.0014, 0.0, filt=lambda p: inHand(p) and sd(p, H + u3 * 0.001, u3) > 0),   # finger splits
    Band(V((0, -0.0045, 0)), V((0, 1, 0)), 0.0014, 0.0, filt=lambda p: inHand(p) and sd(p, H + u3 * 0.001, u3) > 0),
    Band(V((0, 0.0058, 0)), V((0, 1, 0)), 0.0014, 0.0, filt=lambda p: inHand(p) and sd(p, H + u3 * 0.001, u3) > 0),
]

def classify(p):
    res = None
    for f in FEATS:
        c = f.classify(p)
        if c == 'gap': return 'gap'
        if c == 'gold': res = 'gold'
    return res

log("bisecting shell")
bm = bm_from(SHELLBASE)
for f in FEATS:
    for (pt, n) in f.planes():
        geom = [x for x in bm.faces] + [x for x in bm.edges] + [x for x in bm.verts]
        bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-7, plane_co=pt, plane_no=n)
bmesh.ops.dissolve_degenerate(bm, dist=2e-6, edges=bm.edges[:])
log("bisect done, faces", len(bm.faces))
kill = []
for fc in bm.faces:
    c = classify(fc.calc_center_median())
    if c == 'gap': kill.append(fc)
    elif c == 'gold': fc.material_index = 1
    else: fc.material_index = 0
bmesh.ops.delete(bm, geom=kill, context='FACES')
# pauldron: push the shoulder plates outwards to read as a heavier cap
for v in bm.verts:
    if sd(v.co, S + u1 * 0.058, u1) < 0 and d_cut(v.co) > 0.008:
        v.co += v.normal * 0.0045
# drop tiny islands
bm.verts.ensure_lookup_table()
seen = set(); small = []
for fc in bm.faces:
    if fc in seen: continue
    comp = [fc]; seen.add(fc); st = [fc]
    while st:
        g = st.pop()
        for e in g.edges:
            for h in e.link_faces:
                if h not in seen: seen.add(h); comp.append(h); st.append(h)
    if len(comp) < 40: small += comp
bmesh.ops.delete(bm, geom=small, context='FACES')
SHELL = SHELLBASE; SHELL.name = "Robo_Shell"; SHELL.data.name = "Robo_Shell"
bm.to_mesh(SHELL.data); bm.free(); smooth_shade(SHELL.data)
SHELL.data.materials.append(M_IVORY); SHELL.data.materials.append(M_GOLD)
m = SHELL.modifiers.new("solid", 'SOLIDIFY'); m.thickness = 0.0016; m.offset = -1.0
m.use_rim = True; m.material_offset_rim = 1; m.use_even_offset = False
m = SHELL.modifiers.new("bev", 'BEVEL'); m.width = 0.00035; m.segments = 2; m.limit_method = 'ANGLE'
m.angle_limit = math.radians(40); m.harden_normals = False
log("shell done")

# ---------------------------------------------------------------- 3. glow + mechanical details
core_bvh = BVHTree.FromObject(CORE, bpy.context.evaluated_depsgraph_get())
shell_bm = bmesh.new(); shell_bm.from_mesh(SHELL.data)
shell_bvh = BVHTree.FromBMesh(shell_bm)

def hit_from(bvh, origin, direction, dist=0.2):
    loc, nor, idx, d = bvh.ray_cast(origin, direction.normalized(), dist)
    return (loc, nor) if loc is not None else (None, None)

def surf_line(a, b, cdir, bvh, steps, lift):
    pts = []
    ax = (b - a).normalized(); c = (cdir - ax * cdir.dot(ax)).normalized()
    for i in range(steps + 1):
        q = a.lerp(b, i / steps)
        loc, nor = hit_from(bvh, q + c * 0.08, -c)
        if loc is not None: pts.append(loc + nor * lift)
    return pts

# glowing lines in the front seams (sit on the core, inside the seam)
fl = surf_line(E + u2 * 0.016, W - u2 * 0.008, fore_front, core_bvh, 40, 0.0004)
GL1 = poly_tube("Robo_GlowLine_Forearm", smooth_pts(fl, 4), 0.0010, M_BLUE)
ul = surf_line(S + u1 * 0.066, E - u1 * 0.012, V((-0.3, -1, 0)), core_bvh, 40, 0.0004)
GL2 = poly_tube("Robo_GlowLine_UpperArm", smooth_pts(ul, 4), 0.0010, M_BLUE)

# ring loops: core cross-section at a plane -> glowing ring
def core_loop(pt, n, near, maxr=0.05):
    bm = bmesh.new(); bm.from_mesh(CORE.data)
    geom = list(bm.faces) + list(bm.edges) + list(bm.verts)
    r = bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-7, plane_co=pt, plane_no=n)
    cut = [e for e in r['geom_cut'] if isinstance(e, bmesh.types.BMEdge)]
    cut = [e for e in cut if (e.verts[0].co - near).length < maxr]
    adj = {}
    for e in cut:
        a, b = e.verts
        adj.setdefault(a, []).append(b); adj.setdefault(b, []).append(a)
    best = []
    seen = set()
    for v0 in adj:
        if v0 in seen: continue
        loop = [v0]; seen.add(v0); prev = None; cur = v0
        while True:
            nx = [w for w in adj[cur] if w is not prev and w not in seen]
            if not nx: break
            prev, cur = cur, nx[0]; seen.add(cur); loop.append(cur)
        if len(loop) > len(best): best = loop
    pts = [v.co.copy() for v in best]
    bm.free()
    return pts

def ring(name, pt, n, near, rad, lift, mat=M_BLUE):
    pts = core_loop(pt, n, near)
    if len(pts) < 8: log("ring failed", name); return None
    c = sum(pts, V()) / len(pts)
    pts = [p + (p - c).normalized() * lift for p in pts]
    pts = smooth_pts(pts, 3, closed=True)[::2]
    return poly_tube(name, pts, rad, mat, closed=True)

RW = ring("Robo_GlowRing_Wrist", W, nWr, W, 0.0008, 0.0006)
RE1 = ring("Robo_GlowRing_Elbow", E, nEl, E, 0.0007, 0.0005)
RS = ring("Robo_GlowRing_Shoulder", P0 + NCUT * 0.0075, NCUT, S, 0.0007, 0.0005)

# elbow hinge discs (lateral and medial)
hinge = u1.cross(u2).normalized()
if hinge.x > 0: hinge = -hinge          # lateral = -X
def disc_stack(prefix, loc, nrm, r, glow_r, mat_ring=M_GOLD, mat_glow=M_BLUE, depth=0.0018):
    objs = []
    bpy.ops.mesh.primitive_cylinder_add(vertices=40, radius=r, depth=depth)
    base = bpy.context.object; base.name = prefix + "_Base"; base.data.materials.append(M_GUN)
    bpy.ops.mesh.primitive_torus_add(major_segments=48, minor_segments=10, major_radius=r * 0.92, minor_radius=r * 0.12)
    tor = bpy.context.object; tor.name = prefix + "_Trim"; tor.data.materials.append(mat_ring)
    bpy.ops.mesh.primitive_cylinder_add(vertices=40, radius=glow_r, depth=depth * 0.6)
    gl = bpy.context.object; gl.name = prefix + "_Glow"; gl.data.materials.append(mat_glow)
    for o, off in ((base, 0.0), (tor, depth * 0.5), (gl, depth * 0.55)):
        smooth_shade(o.data)
        o.location = loc + nrm * off; o.rotation_euler = nrm.to_track_quat('Z', 'Y').to_euler()
        o.parent = SCULPT
        objs.append(o)
    return objs

for side, nm in ((hinge, "L"), (-hinge, "M")):
    loc, nor = hit_from(core_bvh, E + side * 0.06, -side)
    if loc is not None:
        disc_stack("Robo_ElbowHinge_" + nm, loc + nor * 0.0004, nor, 0.0052, 0.0028)

# shoulder emitter disc on the pauldron (outer side)
loc, nor = hit_from(shell_bvh, V((-0.30, 0.036, 0.742)), V((1, 0, 0)))
log("shoulder disc at", loc, nor)
if loc is not None:
    disc_stack("Robo_ShoulderEmitter", loc + nor * 0.0006, nor, 0.0105, 0.0072, depth=0.0024)

# blue dots: knuckles (MCP), finger joints, wrist and shoulder socket
def dot(name, loc, r=0.0013, mat=M_BLUE):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=r, location=loc)
    o = bpy.context.object; o.name = name; o.data.materials.append(mat); smooth_shade(o.data); o.parent = SCULPT
    return o

DOTS = []
fy = [-0.021, -0.010, 0.0005, 0.0105]
mcp = H + u3 * 0.001
for i, y in enumerate(fy):
    q = V((mcp.x, y, mcp.z + (0.002 if i == 3 else 0)))
    loc, nor = hit_from(core_bvh, q + V((-0.05, 0, 0)), V((1, 0, 0)))
    if loc: DOTS.append(dot("Robo_Dot_MCP%d" % i, loc + nor * 0.0004))
    loc, nor = hit_from(core_bvh, V((-0.22, y, 0.437)), V((1, 0, 0)))
    if loc: DOTS.append(dot("Robo_Dot_PIP%d" % i, loc + nor * 0.0004, 0.0011))
    loc, nor = hit_from(core_bvh, V((-0.159, y, 0.38)), V((0, 0, 1)))
    if loc: DOTS.append(dot("Robo_Dot_DIP%d" % i, loc + nor * 0.0004, 0.0010))
# socket dots
for k in range(7):
    a = -0.9 + k * 0.3
    tdir = V((0, math.cos(a), math.sin(a)))
    tdir = (tdir - NCUT * tdir.dot(NCUT)).normalized()
    c = P0 + NCUT * 0.0075 + V((0, 0.03, 0.06))
    loc, nor = hit_from(core_bvh, c + tdir * 0.08 + NCUT * 0.0, -tdir)
    if loc: DOTS.append(dot("Robo_Dot_Socket%d" % k, loc + nor * 0.0003, 0.0011))
log("dots", len(DOTS))

# gold collar along the marble cut edge: section of the marble just inside the cut plane
def mesh_loop(ob, pt, n, near, maxr=0.07, region=None):
    bm = bmesh.new(); bm.from_mesh(ob.data)
    faces = [f for f in bm.faces if region is None or region(f.verts[0].co)]
    geom = faces + list({e for f in faces for e in f.edges}) + list({v for f in faces for v in f.verts})
    r = bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-7, plane_co=pt, plane_no=n)
    cut = [e for e in r['geom_cut'] if isinstance(e, bmesh.types.BMEdge) and (e.verts[0].co - near).length < maxr]
    adj = {}
    for e in cut:
        a_, b_ = e.verts; adj.setdefault(a_, []).append(b_); adj.setdefault(b_, []).append(a_)
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
cl = mesh_loop(SCULPT, P0 - NCUT * 0.0006, NCUT, S, region=lambda c: c.x < -0.06 and c.z > 0.6)
cpts = smooth_pts(cl, 6, closed=True)[::3]
log("collar pts", len(cpts))
COLLAR = poly_tube("Robo_Collar_Gold", cpts, 0.0022, M_GOLD, closed=True, res=8)
SHELL.data.materials  # noqa

# ---------------------------------------------------------------- 4. headband
log("headband")
co = np.empty(len(SCULPT.data.vertices) * 3); SCULPT.data.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
HC = V((-0.031, -0.002, 0.0))          # head axis (x, y)
FACE = V((0.81, -0.59, 0)).normalized()  # face direction (head turned to his left)
def zband(theta):   # band height as function of polar angle; front a bit higher than back
    d = V((math.cos(theta), math.sin(theta), 0))
    return 0.9465 + 0.0035 * d.dot(FACE)
head = co[(co[:, 2] > 0.90) & (co[:, 2] < 0.99) & (np.hypot(co[:, 0] - HC.x, co[:, 1] - HC.y) < 0.11)]
ang = np.arctan2(head[:, 1] - HC.y, head[:, 0] - HC.x)
rad = np.hypot(head[:, 0] - HC.x, head[:, 1] - HC.y)
NB = 180; BH = 0.0075   # band height
def envelope(zoff, win=0.0018, pct=90):
    rm = np.zeros(NB)
    for i in range(NB):
        th = -math.pi + (i + 0.5) * 2 * math.pi / NB
        zc = zband(th) + zoff
        dth = np.angle(np.exp(1j * (ang - th)))
        m = (np.abs(dth) < 2 * math.pi / NB * 1.5) & (np.abs(head[:, 2] - zc) < win)
        rm[i] = np.percentile(rad[m], pct) if m.sum() > 5 else 0
    for i in range(NB):
        if rm[i] == 0: rm[i] = max(rm[i - 1], rm[(i + 1) % NB])
    e = rm.copy()
    for _ in range(25):
        e = np.maximum(e, rm - 0.0006)
        e = (np.roll(e, 1) + 2 * e + np.roll(e, -1)) / 4
    return np.maximum(e, rm - 0.0008)
ENV_B = envelope(-BH / 2); ENV_T = envelope(BH / 2); ENV_M = envelope(0.0)
envs = np.maximum(ENV_M, (ENV_B + ENV_T) / 2)
log("head radius min/max", envs.min(), envs.max())
# band as a swept rectangle (mesh built directly), with the glowing strip as an inset
def band_mesh(name, r_in, thick, h, mat, zoff=0.0, segs=NB):
    me = D.meshes.new(name); bmb = bmesh.new()
    rings = []
    for i in range(segs):
        th = -math.pi + (i + 0.5) * 2 * math.pi / segs
        d = V((math.cos(th), math.sin(th), 0))
        x = i * NB / segs
        rb = float(np.interp(x, np.arange(NB), ENV_B, period=NB)); rt = float(np.interp(x, np.arange(NB), ENV_T, period=NB))
        rmid = float(np.interp(x, np.arange(NB), envs, period=NB))
        # inner face follows the local slope (bottom/top envelopes), never below the mid envelope
        rb2 = max(rmid + (rb - rt) * 0.5, rmid - 0.004); rt2 = max(rmid - (rb - rt) * 0.5, rmid - 0.004)
        k = h / BH
        rb2 = rmid + (rb2 - rmid) * k; rt2 = rmid + (rt2 - rmid) * k
        rb2 = max(rb2, rb) + r_in if h >= BH else rb2 + r_in; rt2 = max(rt2, rt) + r_in if h >= BH else rt2 + r_in
        zc = zband(th) + zoff
        prof = [(rb2, -h / 2), (rb2 + thick, -h / 2), (rt2 + thick, h / 2), (rt2, h / 2)]
        rings.append([bmb.verts.new(HC + d * pr + V((0, 0, zc + pz))) for pr, pz in prof])
    for i in range(segs):
        a, b = rings[i], rings[(i + 1) % segs]
        for k in range(4):
            bmb.faces.new((a[k], b[k], b[(k + 1) % 4], a[(k + 1) % 4]))
    bmb.normal_update(); bmesh.ops.recalc_face_normals(bmb, faces=bmb.faces)
    bmb.to_mesh(me); bmb.free()
    ob = new_obj(name, me, (mat,))
    smooth_shade(me)
    m = ob.modifiers.new("bev", 'BEVEL'); m.width = 0.0005; m.segments = 2; m.limit_method = 'ANGLE'
    return ob

BAND = band_mesh("Neuro_Band", 0.0003, 0.0022, BH, M_AMBER_GOLD)
BANDGLOW = band_mesh("Neuro_Band_Glow", 0.0020, 0.0008, 0.0030, M_AMBER)
for o in (BAND, BANDGLOW):
    o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
# modules: front (face dir), both temples, back
def band_point(th, extra):
    i = ((th + math.pi) / (2 * math.pi) * NB - 0.5) % NB
    r = float(np.interp(i, np.arange(NB), envs, period=NB))
    d = V((math.cos(th), math.sin(th), 0))
    return HC + d * (r + extra) + V((0, 0, zband(th))), d
fa = math.atan2(FACE.y, FACE.x)
MODS = []
for nm, off, rr in (("Front", 0.0, 0.0085), ("TempleL", math.radians(78), 0.0070),
                    ("TempleR", math.radians(-78), 0.0070), ("Back", math.pi, 0.0075)):
    p, d = band_point(fa + off, 0.0034)
    objs = []
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=rr, depth=0.0034)
    b = bpy.context.object; b.name = "Neuro_Module_%s" % nm; b.data.materials.append(M_AMBER_GOLD)
    bv = b.modifiers.new("bev", 'BEVEL'); bv.width = 0.0006; bv.segments = 3
    bpy.ops.mesh.primitive_torus_add(major_segments=48, minor_segments=10, major_radius=rr * 0.68, minor_radius=rr * 0.11)
    t = bpy.context.object; t.name = "Neuro_Module_%s_GlowRing" % nm; t.data.materials.append(M_AMBER)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=rr * 0.48)
    l = bpy.context.object; l.name = "Neuro_Module_%s_Lens" % nm; l.data.materials.append(M_LENS)
    l.scale = (1, 1, 0.45)
    for o, off2 in ((b, 0.0), (t, 0.0017), (l, 0.0016)):
        smooth_shade(o.data)
        o.location = p + d * off2; o.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
        o.parent = SCULPT
    MODS.append(b)
log("headband done")

# ---------------------------------------------------------------- 5. cleanup / organise
D.objects.remove(ARMREF, do_unlink=True)
col = D.collections.get("Cyber") or D.collections.new("Cyber")
if col.name not in SC.collection.children: SC.collection.children.link(col)
for o in list(SC.collection.objects):
    if o.name.startswith(("Robo_", "Neuro_")):
        SC.collection.objects.unlink(o); col.objects.link(o)
        o.matrix_parent_inverse = SCULPT.matrix_world.inverted()
SCULPT["cyber"] = 1
log("objects", len(col.objects))
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
log("saved", OUT)
