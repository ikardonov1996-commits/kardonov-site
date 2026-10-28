# Build "marble block hanging on rope from a hand-cranked windlass" scene.
# Run: blender -b assets/asset_block.blend -P scripts/rope_build.py -- <out.blend>
import bpy, math, sys
import numpy as np
from mathutils import Vector, Matrix

argv = sys.argv[sys.argv.index("--") + 1:]
OUT = argv[0]

# ---------------- constants (metres / radians) ----------------
Z_AX = 1.05            # drum axis height above the sills' bottom
R_DRUM = 0.09          # drum radius (0.18 m diameter)
R_ROPE = 0.015         # main rope radius (30 mm hemp)
R_EFF = R_DRUM + R_ROPE
PITCH = 0.031          # helix advance per turn on the drum
DROP = 3.0             # total drop for descent 0 -> 1
L0 = 0.35              # free rope length (drum tangent -> bundle top) at descent 0
W0 = 8 * 2 * math.pi   # wound angle at descent 0 (8 turns)
XD0 = 0.07             # x of rope departure point at descent 0
LAY = 0.10             # lay length of 3-strand rope
APEX_H = 0.42          # height of the sling apex above block top
RHO = 0.03             # radial offset of the 4 sling legs inside the bundle
LASH_H = 0.10          # height of the lashing that binds the legs
FPS, F0, F1 = 30, 1, 240
TAU = 2 * math.pi

sc = bpy.context.scene
sc.cursor.location = (0, 0, 0)
O = bpy.data.objects
for n in ("Floor", "Key", "Fill", "Rim"):
    if n in O:
        bpy.data.objects.remove(O[n], do_unlink=True)

coll = bpy.data.collections.new("Rope_Windlass")
sc.collection.children.link(coll)

def link(ob):
    for c in ob.users_collection:
        c.objects.unlink(ob)
    coll.objects.link(ob)
    return ob

# ---------------- materials ----------------
def mat_wood():
    m = bpy.data.materials.new("Wood_Aged"); m.use_nodes = True
    nt = m.node_tree; N = nt.nodes; L = nt.links.new
    b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1.2, 16.0, 16.0)
    L(tc.outputs["Object"], mp.inputs["Vector"])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 2.5
    nz.inputs["Detail"].default_value = 10; nz.inputs["Roughness"].default_value = 0.62
    nz.inputs["Distortion"].default_value = 0.6
    L(mp.outputs["Vector"], nz.inputs["Vector"])
    cr = N.new("ShaderNodeValToRGB"); e = cr.color_ramp.elements
    e[0].position = 0.30; e[0].color = (0.075, 0.062, 0.050, 1)
    e[1].position = 0.70; e[1].color = (0.36, 0.33, 0.29, 1)
    mid = e.new(0.5); mid.color = (0.19, 0.155, 0.12, 1)
    L(nz.outputs["Fac"], cr.inputs["Fac"])
    L(cr.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.82
    nb = N.new("ShaderNodeTexNoise"); nb.inputs["Scale"].default_value = 9.0; nb.inputs["Detail"].default_value = 12
    L(mp.outputs["Vector"], nb.inputs["Vector"])
    bump = N.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.35; bump.inputs["Distance"].default_value = 0.004
    L(nb.outputs["Fac"], bump.inputs["Height"]); L(bump.outputs["Normal"], b.inputs["Normal"])
    return m

def mat_iron():
    m = bpy.data.materials.new("Iron_Dark"); m.use_nodes = True
    nt = m.node_tree; N = nt.nodes; L = nt.links.new
    b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord")
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 18; nz.inputs["Detail"].default_value = 8
    L(tc.outputs["Object"], nz.inputs["Vector"])
    cr = N.new("ShaderNodeValToRGB"); e = cr.color_ramp.elements
    e[0].position = 0.55; e[0].color = (0.045, 0.043, 0.041, 1)
    e[1].position = 0.75; e[1].color = (0.16, 0.075, 0.035, 1)
    L(nz.outputs["Fac"], cr.inputs["Fac"]); L(cr.outputs["Color"], b.inputs["Base Color"])
    rr = N.new("ShaderNodeMapRange"); rr.inputs["From Min"].default_value = 0.55; rr.inputs["From Max"].default_value = 0.75
    rr.inputs["To Min"].default_value = 0.5; rr.inputs["To Max"].default_value = 0.9
    L(nz.outputs["Fac"], rr.inputs["Value"]); L(rr.outputs["Result"], b.inputs["Roughness"])
    mm = N.new("ShaderNodeMapRange"); mm.inputs["From Min"].default_value = 0.55; mm.inputs["From Max"].default_value = 0.75
    mm.inputs["To Min"].default_value = 0.9; mm.inputs["To Max"].default_value = 0.2
    L(nz.outputs["Fac"], mm.inputs["Value"]); L(mm.outputs["Result"], b.inputs["Metallic"])
    return m

def mat_rope():
    m = bpy.data.materials.new("Rope_Hemp"); m.use_nodes = True
    nt = m.node_tree; N = nt.nodes; L = nt.links.new
    b = N["Principled BSDF"]
    at = N.new("ShaderNodeAttribute"); at.attribute_name = "ropeU"
    nz = N.new("ShaderNodeTexNoise"); nz.noise_dimensions = "1D"
    nz.inputs["Scale"].default_value = 3.0; nz.inputs["Detail"].default_value = 4
    L(at.outputs["Fac"], nz.inputs["W"])
    cr = N.new("ShaderNodeValToRGB"); e = cr.color_ramp.elements
    e[0].position = 0.35; e[0].color = (0.30, 0.22, 0.13, 1)
    e[1].position = 0.65; e[1].color = (0.46, 0.36, 0.23, 1)
    L(nz.outputs["Fac"], cr.inputs["Fac"])
    # fine fibre noise darkening the crevices a bit
    tc = N.new("ShaderNodeTexCoord")
    nf = N.new("ShaderNodeTexNoise"); nf.inputs["Scale"].default_value = 260; nf.inputs["Detail"].default_value = 6
    L(tc.outputs["Object"], nf.inputs["Vector"])
    mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"
    mx.inputs["Factor"].default_value = 0.35
    L(cr.outputs["Color"], mx.inputs["A"]); L(nf.outputs["Color"], mx.inputs["B"])
    L(mx.outputs["Result"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.92
    b.inputs["Sheen Weight"].default_value = 0.4
    bump = N.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.5; bump.inputs["Distance"].default_value = 0.0015
    L(nf.outputs["Fac"], bump.inputs["Height"]); L(bump.outputs["Normal"], b.inputs["Normal"])
    return m

M_WOOD, M_IRON, M_ROPE = mat_wood(), mat_iron(), mat_rope()

# ---------------- geometry nodes: 3-strand rope from any curve ----------------
def gsock(ng, name, kind, io="INPUT", default=None):
    s = ng.interface.new_socket(name=name, in_out=io, socket_type=kind)
    if default is not None:
        s.default_value = default
    return s

class B:
    def __init__(self, ng):
        self.ng = ng; self.N = ng.nodes; self.l = ng.links.new
    def node(self, t, **kw):
        n = self.N.new(t)
        for k, v in kw.items():
            setattr(n, k, v)
        return n
    def _in(self, sock, v):
        if isinstance(v, bpy.types.NodeSocket):
            self.l(v, sock)
        else:
            sock.default_value = v
    def math(self, op, a, b=None):
        n = self.node("ShaderNodeMath", operation=op)
        self._in(n.inputs[0], a)
        if b is not None:
            self._in(n.inputs[1], b)
        return n.outputs[0]
    def vmath(self, op, a, b=None, scale=None):
        n = self.node("ShaderNodeVectorMath", operation=op)
        self._in(n.inputs[0], a)
        if b is not None:
            self._in(n.inputs[1], b)
        if scale is not None:
            self._in(n.inputs[3], scale)
        return n.outputs[0] if op != "DOT_PRODUCT" else n.outputs[1]
    def xyz(self, x, y, z):
        n = self.node("ShaderNodeCombineXYZ")
        for i, v in enumerate((x, y, z)):
            self._in(n.inputs[i], v)
        return n.outputs[0]

def build_strands():
    ng = bpy.data.node_groups.new("RopeStrands", "GeometryNodeTree")
    gsock(ng, "Geometry", "NodeSocketGeometry")
    gsock(ng, "U Offset", "NodeSocketFloat", default=0.0)
    gsock(ng, "Rope Radius", "NodeSocketFloat", default=R_ROPE)
    gsock(ng, "Lay Length", "NodeSocketFloat", default=LAY)
    gsock(ng, "Spacing", "NodeSocketFloat", default=0.006)
    gsock(ng, "Material", "NodeSocketMaterial")
    gsock(ng, "Geometry", "NodeSocketGeometry", io="OUTPUT")
    b = B(ng)
    gi = b.node("NodeGroupInput"); go = b.node("NodeGroupOutput")
    rs = b.node("GeometryNodeResampleCurve"); rs.mode = "LENGTH"
    b.l(gi.outputs["Geometry"], rs.inputs["Curve"]); b.l(gi.outputs["Spacing"], rs.inputs["Length"])
    sp = b.node("GeometryNodeSplineParameter"); sl = b.node("GeometryNodeSplineLength")
    U = b.math("ADD", b.math("SUBTRACT", sl.outputs["Length"], sp.outputs["Length"]), gi.outputs["U Offset"])
    st = b.node("GeometryNodeStoreNamedAttribute", data_type="FLOAT", domain="POINT")
    st.inputs["Name"].default_value = "ropeU"
    b.l(rs.outputs[0], st.inputs["Geometry"]); b.l(U, st.inputs["Value"])
    tan = b.node("GeometryNodeInputTangent").outputs[0]
    nor = b.node("GeometryNodeInputNormal").outputs[0]
    bn = b.vmath("CROSS_PRODUCT", tan, nor)
    s = b.math("MULTIPLY", gi.outputs["Rope Radius"], 0.5)
    ph = b.math("MULTIPLY", b.math("DIVIDE", U, gi.outputs["Lay Length"]), TAU)
    circ = b.node("GeometryNodeCurvePrimitiveCircle", mode="RADIUS")
    circ.inputs["Resolution"].default_value = 8
    b.l(s, circ.inputs["Radius"])
    join = b.node("GeometryNodeJoinGeometry")
    for i in range(3):
        a = b.math("ADD", ph, i * TAU / 3)
        off = b.vmath("ADD", b.vmath("SCALE", nor, scale=b.math("COSINE", a)),
                      b.vmath("SCALE", bn, scale=b.math("SINE", a)))
        off = b.vmath("SCALE", off, scale=s)
        spn = b.node("GeometryNodeSetPosition")
        b.l(st.outputs[0], spn.inputs["Geometry"]); b.l(off, spn.inputs["Offset"])
        c2m = b.node("GeometryNodeCurveToMesh")
        b.l(spn.outputs[0], c2m.inputs["Curve"]); b.l(circ.outputs["Curve"], c2m.inputs["Profile Curve"])
        c2m.inputs["Fill Caps"].default_value = True
        b.l(c2m.outputs["Mesh"], join.inputs[0])
    sm = b.node("GeometryNodeSetShadeSmooth"); b.l(join.outputs[0], sm.inputs["Geometry"])
    smat = b.node("GeometryNodeSetMaterial"); b.l(sm.outputs[0], smat.inputs["Geometry"])
    b.l(gi.outputs["Material"], smat.inputs["Material"])
    b.l(smat.outputs[0], go.inputs[0])
    return ng

NG_STRANDS = build_strands()

def strands_node(b, curve_sock, uoff, radius=R_ROPE, lay=LAY, spacing=0.006):
    g = b.node("GeometryNodeGroup"); g.node_tree = NG_STRANDS
    b.l(curve_sock, g.inputs["Geometry"])
    b._in(g.inputs["U Offset"], uoff)
    g.inputs["Rope Radius"].default_value = radius
    g.inputs["Lay Length"].default_value = lay
    g.inputs["Spacing"].default_value = spacing
    g.inputs["Material"].default_value = M_ROPE
    return g.outputs[0]

def build_line_group():
    """Vertical free rope: from object origin straight down by Length."""
    ng = bpy.data.node_groups.new("RopeFreeSpan", "GeometryNodeTree")
    gsock(ng, "Geometry", "NodeSocketGeometry")
    gsock(ng, "Length", "NodeSocketFloat", default=L0)
    gsock(ng, "Geometry", "NodeSocketGeometry", io="OUTPUT")
    b = B(ng); gi = b.node("NodeGroupInput"); go = b.node("NodeGroupOutput")
    cl = b.node("GeometryNodeCurvePrimitiveLine")
    cl.inputs["Start"].default_value = (0, 0, 0)
    b.l(b.xyz(0.0, 0.0, b.math("MULTIPLY", gi.outputs["Length"], -1.0)), cl.inputs["End"])
    b.l(strands_node(b, cl.outputs[0], 0.0), go.inputs[0])
    return ng

def build_coil_group():
    """Rope wound on the drum, in windlass space (origin on drum axis, not rotating).
    Wound part spans phi in [-W, 0]; phi=0 is the front tangent point where the rope leaves downward."""
    ng = bpy.data.node_groups.new("RopeDrumCoil", "GeometryNodeTree")
    gsock(ng, "Geometry", "NodeSocketGeometry")
    gsock(ng, "Wound Angle", "NodeSocketFloat", default=W0)
    gsock(ng, "X Departure", "NodeSocketFloat", default=XD0)
    gsock(ng, "U Offset", "NodeSocketFloat", default=L0)
    gsock(ng, "Geometry", "NodeSocketGeometry", io="OUTPUT")
    b = B(ng); gi = b.node("NodeGroupInput"); go = b.node("NodeGroupOutput")
    cl = b.node("GeometryNodeCurvePrimitiveLine")
    rs = b.node("GeometryNodeResampleCurve"); rs.mode = "COUNT"
    b.l(cl.outputs[0], rs.inputs["Curve"])
    b.l(b.math("ADD", b.math("MULTIPLY", gi.outputs["Wound Angle"], 72 / TAU), 2.0), rs.inputs["Count"])
    t = b.node("GeometryNodeSplineParameter").outputs["Factor"]
    phi = b.math("MULTIPLY", b.math("SUBTRACT", t, 1.0), gi.outputs["Wound Angle"])
    x = b.math("ADD", gi.outputs["X Departure"], b.math("MULTIPLY", phi, PITCH / TAU))
    y = b.math("MULTIPLY", b.math("COSINE", phi), -R_EFF)
    z = b.math("MULTIPLY", b.math("SINE", phi), -R_EFF)
    spn = b.node("GeometryNodeSetPosition")
    b.l(rs.outputs[0], spn.inputs["Geometry"]); b.l(b.xyz(x, y, z), spn.inputs["Position"])
    b.l(strands_node(b, spn.outputs[0], gi.outputs["U Offset"]), go.inputs[0])
    return ng

NG_LINE, NG_COIL = build_line_group(), build_coil_group()

def sock_id(ng, name):
    return ng.interface.items_tree[name].identifier

def rope_curve_obj(name, pts, parent=None, radius=R_ROPE, lay=LAY, spacing=0.006):
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"; cu.twist_mode = "MINIMUM"
    sp = cu.splines.new("POLY"); sp.points.add(len(pts) - 1)
    for p, q in zip(sp.points, pts):
        p.co = (q[0], q[1], q[2], 1.0)
    ob = bpy.data.objects.new(name, cu); coll.objects.link(ob)
    md = ob.modifiers.new("Rope", "NODES"); md.node_group = NG_STRANDS
    md[sock_id(NG_STRANDS, "Rope Radius")] = radius
    md[sock_id(NG_STRANDS, "Lay Length")] = lay
    md[sock_id(NG_STRANDS, "Spacing")] = spacing
    md[sock_id(NG_STRANDS, "Material")] = M_ROPE
    if parent:
        ob.parent = parent
    return ob

# ---------------- block analysis + harness ----------------
blk = O["Marble_Block"]; root = O["Marble_Root"]
me = blk.data
co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
mw = np.array(blk.matrix_world); co = co @ mw[:3, :3].T + mw[:3, 3]
me.calc_loop_triangles()
tri = np.empty(len(me.loop_triangles) * 3, dtype=np.int64); me.loop_triangles.foreach_get("vertices", tri)
tri = tri.reshape(-1, 3)
a, bb, c = co[tri[:, 0]], co[tri[:, 1]], co[tri[:, 2]]
vol = np.einsum("ij,ij->i", a, np.cross(bb, c)) / 6.0
com = ((a + bb + c) / 4.0 * vol[:, None]).sum(0) / vol.sum()
cx, cy = float(com[0]), float(com[1])
top = float(co[:, 2].max()); bot = float(co[:, 2].min())
ZA = top + APEX_H; ZT = ZA + LASH_H
print("COM", com, "top", top, "bot", bot, "ZA", ZA, "ZT", ZT, "vol", vol.sum())

def hull2d(P):
    P = sorted(set(map(tuple, np.round(P, 5))))
    def cross(o, a, b): return (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0])
    lo, up = [], []
    for p in P:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 1e-12: lo.pop()
        lo.append(p)
    for p in reversed(P):
        while len(up) >= 2 and cross(up[-2], up[-1], p) <= 1e-12: up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]   # CCW

def sling_path(axis, extra_off=None):
    """Taut sling in the plane through the COM: convex hull of the block slab + the two apex points,
    offset outward by the rope radius. Returns 2D (u,z) path from left apex around the bottom to right apex."""
    if axis == "x":
        m = np.abs(co[:, 1] - cy) < R_ROPE; U = co[m, 0]; uc = cx
    else:
        m = np.abs(co[:, 0] - cx) < R_ROPE; U = co[m, 1]; uc = cy
    P = np.c_[U, co[m, 2]]
    apL, apR = (round(uc - RHO, 5), round(ZA, 5)), (round(uc + RHO, 5), round(ZA, 5))
    H = hull2d(np.vstack([P, [apL, apR]]))
    i0 = H.index(apL); H = H[i0:] + H[:i0]
    i1 = H.index(apR); H = H[:i1 + 1]
    H = [np.array(h) for h in H]
    r = R_ROPE * 0.97
    out = [H[0]]
    for k in range(1, len(H) - 1):
        d1 = H[k] - H[k-1]; d2 = H[k+1] - H[k]
        n1 = np.array([d1[1], -d1[0]]) / np.linalg.norm(d1)
        n2 = np.array([d2[1], -d2[0]]) / np.linalg.norm(d2)
        a1, a2 = math.atan2(n1[1], n1[0]), math.atan2(n2[1], n2[0])
        da = (a2 - a1 + math.pi) % TAU - math.pi
        steps = max(1, int(abs(da) / math.radians(12)) + 1)
        for s in range(steps + 1):
            ang = a1 + da * s / steps
            out.append(H[k] + r * np.array([math.cos(ang), math.sin(ang)]))
    out.append(H[-1])
    # drop points closer than 4 mm
    clean = [out[0]]
    for p in out[1:]:
        if np.linalg.norm(p - clean[-1]) > 0.004:
            clean.append(p)
    if np.linalg.norm(clean[-1] - out[-1]) > 1e-9:
        clean[-1] = out[-1]
    return np.array(clean), uc

pa, ucA = sling_path("x")
pb, ucB = sling_path("y")

def bottom_z(path, uc):
    lowpts = path[path[:, 1] < bot + 0.15]
    i = np.argmin(np.abs(lowpts[:, 0] - uc)); return lowpts[i, 1]
need = bottom_z(pb, ucB) - (bottom_z(pa, ucA) - 2 * R_ROPE)
if need > 0:   # sling B passes under sling A where they cross below the block
    lowmask = pb[:, 1] < bot + 0.15
    pb[lowmask, 1] -= need * np.exp(-((pb[lowmask, 0] - ucB) / 0.14) ** 2)
print("crossing lift", need)

def to3d(path, axis):
    if axis == "x":
        return [(u, cy, z) for u, z in path]
    return [(cx, u, z) for u, z in path]

def leg_ext(p3, axis, sign):
    # vertical leg inside the lashing bundle, from the apex to just above the lashing
    u = (ucA if axis == "x" else ucB) + sign * RHO
    q = (u, cy, 0) if axis == "x" else (cx, u, 0)
    return [(q[0], q[1], ZT + 0.012), (q[0], q[1], ZA + 0.03)]

A3 = to3d(pa, "x"); B3 = to3d(pb, "y")
A3 = leg_ext(None, "x", -1) + A3[1:-1] + leg_ext(None, "x", +1)[::-1]
B3 = leg_ext(None, "y", -1) + B3[1:-1] + leg_ext(None, "y", +1)[::-1]
slA = rope_curve_obj("Sling_A", A3, parent=root, spacing=0.005)
slB = rope_curve_obj("Sling_B", B3, parent=root, spacing=0.005)
# end of the main rope continues down inside the bundle
tail = rope_curve_obj("Rope_Tail", [(cx, cy, ZT + 0.001), (cx, cy, ZA + 0.01)], parent=root, spacing=0.005)
# lashing (seizing) cord binding the four legs + rope end together
RL = RHO + R_ROPE + 0.0055; turns = 7.5; z0, z1 = ZA + 0.004, ZT - 0.006
lash = []
nseg = int(turns * 40)
for i in range(nseg + 1):
    t = i / nseg; ph = t * turns * TAU + 0.3
    lash.append((cx + RL * math.cos(ph), cy + RL * math.sin(ph), z0 + (z1 - z0) * t))
# tuck the end of the cord under the last turn
lash.append((cx + (RL - 0.004) * math.cos(0.3 + turns * TAU + 0.5), cy + (RL - 0.004) * math.sin(0.3 + turns * TAU + 0.5), z1 - 0.012))
lashing = rope_curve_obj("Rope_Lashing", lash, parent=root, radius=0.0055, lay=0.035, spacing=0.003)
for ob in (slA, slB, tail, lashing):
    ob.matrix_parent_inverse = Matrix.Identity(4)

# ---------------- windlass ----------------
def mesh_obj(name, mat, parent=None):
    ob = bpy.context.active_object; ob.name = name; ob.data.name = name
    ob.data.materials.append(mat); link(ob)
    if parent:
        ob.parent = parent; ob.matrix_parent_inverse = parent.matrix_world.inverted()
    for p in ob.data.polygons:
        p.use_smooth = False
    return ob

def beam(name, p1, p2, w, h, mat=M_WOOD, up=(0, 0, 1)):
    p1, p2 = Vector(p1), Vector(p2); d = p2 - p1
    bpy.ops.mesh.primitive_cube_add(size=1)
    ob = mesh_obj(name, mat)
    ob.data.transform(Matrix.Diagonal((d.length, w, h, 1)))
    q = d.to_track_quat("X", "Z")
    ob.rotation_mode = "QUATERNION"; ob.rotation_quaternion = q; ob.location = (p1 + p2) / 2
    bv = ob.modifiers.new("Bevel", "BEVEL"); bv.width = min(w, h) * 0.08; bv.segments = 2
    return ob

def cyl_x(name, x0, x1, r, mat, parent=None, verts=48, smooth=True):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=x1 - x0, location=((x0 + x1) / 2, 0, 0),
                                        rotation=(0, math.pi / 2, 0))
    ob = bpy.context.active_object
    ob.data.transform(ob.matrix_basis); ob.matrix_basis = Matrix.Identity(4)
    ob = mesh_obj(name, mat)
    if smooth:
        for p in ob.data.polygons:
            p.use_smooth = abs(p.normal.x) < 0.5
    if parent:
        ob.parent = parent; ob.matrix_parent_inverse = Matrix.Identity(4)
    bv = ob.modifiers.new("Bevel", "BEVEL"); bv.width = min(0.004, r * 0.2); bv.segments = 2
    bv.limit_method = "ANGLE"
    return ob

PX = 0.70        # post centre x
frame = []
for sx in (-1, 1):
    x = sx * PX
    frame.append(beam("Sill_%s" % ("L" if sx < 0 else "R"), (x, -0.68, 0.07), (x, 0.68, 0.07), 0.18, 0.14))
    nm = "L" if sx < 0 else "R"
    frame.append(beam("Post_" + nm, (x, 0, 0.14), (x, 0, Z_AX + 0.16), 0.16, 0.16))
    for sy in (-1, 1):
        frame.append(beam("Knee_%s%s" % (nm, "F" if sy < 0 else "B"), (x, sy * 0.50, 0.14), (x, sy * 0.06, 0.62), 0.10, 0.10))
frame.append(beam("Stretcher_Back", (-PX - 0.09, 0.52, 0.20), (PX + 0.09, 0.52, 0.20), 0.11, 0.12))

bpy.context.view_layer.update()
wl = bpy.data.objects.new("Windlass", None); coll.objects.link(wl); wl.empty_display_size = 0.3
for f in frame:
    mwf = f.matrix_world.copy(); f.parent = wl; f.matrix_world = mwf

# axle-centred rotating group
drum = None
bpy.ops.mesh.primitive_cylinder_add(vertices=56, radius=R_DRUM, depth=1.16, rotation=(0, math.pi / 2, 0))
drum = bpy.context.active_object; drum.data.transform(drum.matrix_basis); drum.matrix_basis = Matrix.Identity(4)
drum = mesh_obj("Drum", M_WOOD)
for p in drum.data.polygons:
    p.use_smooth = abs(p.normal.x) < 0.5
bv = drum.modifiers.new("Bevel", "BEVEL"); bv.width = 0.006; bv.segments = 2; bv.limit_method = "ANGLE"
drum.location = (0, 0, Z_AX); drum.parent = wl
cyl_x("Drum_Flange_L", -0.60, -0.56, 0.135, M_WOOD, drum, verts=12, smooth=False)
cyl_x("Drum_Flange_R", 0.56, 0.60, 0.135, M_WOOD, drum, verts=12, smooth=False)
cyl_x("Drum_Band_L", -0.55, -0.525, R_DRUM + 0.003, M_IRON, drum)
cyl_x("Drum_Band_R", 0.525, 0.55, R_DRUM + 0.003, M_IRON, drum)
cyl_x("Drum_Band_FL", -0.625, -0.605, 0.12, M_IRON, drum, verts=32)
cyl_x("Drum_Band_FR", 0.605, 0.625, 0.12, M_IRON, drum, verts=32)
cyl_x("Axle", -0.84, 0.90, 0.024, M_IRON, drum)
cyl_x("Axle_Collar_L", -0.82, -0.79, 0.04, M_IRON, drum)
cyl_x("Axle_Collar_R", 0.79, 0.82, 0.04, M_IRON, drum)
# crank: square boss + bent iron bar + wooden grip
bpy.ops.mesh.primitive_cube_add(size=1); boss = mesh_obj("Crank_Boss", M_IRON)
boss.data.transform(Matrix.Diagonal((0.06, 0.08, 0.08, 1)))
boss.parent = drum; boss.matrix_parent_inverse = Matrix.Identity(4); boss.location = (0.875, 0, 0)
bv = boss.modifiers.new("Bevel", "BEVEL"); bv.width = 0.008; bv.segments = 2
ARM = 0.36
def fillet_path(P, rad=0.035, n=6):
    P = [Vector(p) for p in P]; out = [P[0]]
    for i in range(1, len(P) - 1):
        a = (P[i-1] - P[i]).normalized(); c = (P[i+1] - P[i]).normalized()
        s, e = P[i] + a * rad, P[i] + c * rad
        for k in range(n + 1):
            t = k / n
            out.append((1-t)**2 * s + 2*(1-t)*t * P[i] + t*t * e)
    out.append(P[-1]); return out
cpts = fillet_path([(0.86, 0, 0), (0.91, 0, 0), (0.91, 0, ARM), (1.10, 0, ARM)])
ccu = bpy.data.curves.new("Crank", "CURVE"); ccu.dimensions = "3D"; ccu.bevel_depth = 0.017
ccu.bevel_resolution = 3; ccu.use_fill_caps = True
sp = ccu.splines.new("POLY"); sp.points.add(len(cpts) - 1)
for p, q in zip(sp.points, cpts):
    p.co = (q.x, q.y, q.z, 1)
crank = bpy.data.objects.new("Crank", ccu); coll.objects.link(crank); ccu.materials.append(M_IRON)
crank.parent = drum
grip = cyl_x("Crank_Grip", 0.94, 1.08, 0.026, M_WOOD, drum, verts=24)
grip.location = (0, 0, ARM)
for p in grip.data.polygons:
    p.use_smooth = abs(p.normal.x) < 0.5

# ---------------- rig ----------------
dc = bpy.data.objects.new("Descent_Control", None); coll.objects.link(dc)
dc.empty_display_type = "SINGLE_ARROW"; dc.empty_display_size = 0.4; dc.location = (-1.1, 0, 1.3)
dc["descent"] = 0.0
ui = dc.id_properties_ui("descent"); ui.update(min=0.0, max=1.0, soft_min=0.0, soft_max=1.0,
                                               description="0 = block up at the windlass, 1 = fully lowered")
dc["drop_m"] = DROP; dc["drum_radius_eff_m"] = R_EFF; dc["rope_len0_m"] = L0
dc.hide_render = True

piv = bpy.data.objects.new("Hang_Pivot", None); coll.objects.link(piv); piv.empty_display_size = 0.12
piv.location = (XD0, -R_EFF, Z_AX)
drop_e = bpy.data.objects.new("Hang_Drop", None); coll.objects.link(drop_e); drop_e.empty_display_size = 0.15
drop_e.parent = piv; drop_e.location = (0, 0, -L0)
root.parent = drop_e; root.matrix_parent_inverse = Matrix.Identity(4)
root.location = (-cx, -cy, -ZT)

free = bpy.data.objects.new("Rope_FreeSpan", bpy.data.meshes.new("Rope_FreeSpan")); coll.objects.link(free)
free.parent = piv
mfree = free.modifiers.new("Rope", "NODES"); mfree.node_group = NG_LINE
coil = bpy.data.objects.new("Rope_DrumCoil", bpy.data.meshes.new("Rope_DrumCoil")); coll.objects.link(coil)
coil.parent = wl; coil.location = (0, 0, Z_AX)
mcoil = coil.modifiers.new("Rope", "NODES"); mcoil.node_group = NG_COIL

def drv(idb, path, expr, index=-1):
    fc = idb.driver_add(path, index) if index >= 0 else idb.driver_add(path)
    d = fc.driver; d.type = "SCRIPTED"
    v = d.variables.new(); v.name = "d"; v.type = "SINGLE_PROP"
    v.targets[0].id = dc; v.targets[0].data_path = '["descent"]'
    d.expression = expr
    return fc

K_TH = DROP / R_EFF                       # drum angle at descent=1
K_X = K_TH / TAU * PITCH                  # departure walk along the drum
drv(drum, "rotation_euler", "d*%.6f" % K_TH, 0)
drv(piv, "location", "%.6f - d*%.6f" % (XD0, K_X), 0)
drv(drop_e, "location", "-(%.6f + d*%.6f)" % (L0, DROP), 2)
drv(free, 'modifiers["Rope"]["%s"]' % sock_id(NG_LINE, "Length"), "%.6f + d*%.6f" % (L0, DROP))
drv(coil, 'modifiers["Rope"]["%s"]' % sock_id(NG_COIL, "Wound Angle"), "%.6f - d*%.6f" % (W0, K_TH))
drv(coil, 'modifiers["Rope"]["%s"]' % sock_id(NG_COIL, "X Departure"), "%.6f - d*%.6f" % (XD0, K_X))
drv(coil, 'modifiers["Rope"]["%s"]' % sock_id(NG_COIL, "U Offset"), "%.6f + d*%.6f" % (L0, DROP))

# default timeline: descent 0 -> 1 with ease in/out
sc.render.fps = FPS; sc.frame_start = F0; sc.frame_end = F1
dc["descent"] = 0.0; dc.keyframe_insert('["descent"]', frame=F0)
dc["descent"] = 1.0; dc.keyframe_insert('["descent"]', frame=F1)
fcd = dc.animation_data.action.fcurves.find('["descent"]')
for k in fcd.keyframe_points:
    k.interpolation = "BEZIER"; k.handle_left_type = k.handle_right_type = "AUTO_CLAMPED"
fcd.update()

# ---------------- swing: small-angle variable-length pendulum, baked ----------------
D_COM = ZT - float(com[2])      # bundle top -> centre of mass
g = 9.81
def desc_at(t):  # t in seconds
    return fcd.evaluate(F0 + t * FPS)
SUB = 20; dt = 1.0 / (FPS * SUB); T_end = (F1 - F0) / FPS
rng = np.random.default_rng(7)
# smooth "wind / hand" disturbance: sum of a few slow sines
wind = [(rng.uniform(0.15, 0.45), rng.uniform(0, TAU), rng.uniform(0.022, 0.034)) for _ in range(4)]
al, be = math.radians(2.6), math.radians(-0.8)       # alpha: about X (block moves +-Y), beta: about Y (+-X)
ald, bed = 0.0, math.radians(1.6)
ps, psd = math.radians(3.5), 0.0                      # twist about rope axis
w_t = TAU / 5.8; c_sw = 0.015; c_tw = 0.10
keys_a, keys_b, keys_p = [], [], []
t = 0.0
prev = [desc_at(-dt), desc_at(0.0)]
for f in range(F0, F1 + 1):
    keys_a.append(al); keys_b.append(be); keys_p.append(ps)
    if f == F1:
        break
    for s in range(SUB):
        d0, d1, d2 = desc_at(t - dt), desc_at(t), desc_at(t + dt)
        v = (d2 - d0) / (2 * dt) * DROP; acc = (d2 - 2 * d1 + d0) / dt ** 2 * DROP
        L = L0 + d1 * DROP + D_COM; Ld = v
        th = d1 * K_TH; thd = v / R_EFF
        geff = g - acc                                 # lowering acceleration lightens the pendulum
        xacc = -acc / R_EFF / TAU * PITCH              # departure point walking along the drum
        jig = 0.08 * (thd / (K_TH / 4.0))              # hand-cranking jiggle, ~1 per crank turn
        fy = jig * math.sin(th) + 1.7 * sum(A * math.sin(TAU * fr * t + p0) for fr, p0, A in wind)
        fx = 0.6 * jig * math.cos(th) + 1.3 * sum(A * math.cos(TAU * fr * 1.3 * t + p0) for fr, p0, A in wind)
        add = -(geff / L) * al - (2 * Ld / L + c_sw) * ald + fy / L
        bdd = -(geff / L) * be - (2 * Ld / L + c_sw) * bed - (fx - xacc) / L
        pdd = -w_t ** 2 * ps - c_tw * psd + 0.010 * thd * math.cos(0.7 * t)   # rope untwisting while paying out
        ald += add * dt; bed += bdd * dt; psd += pdd * dt
        al += ald * dt; be += bed * dt; ps += psd * dt
        t += dt
ka, kb, kp = map(np.degrees, (keys_a, keys_b, keys_p))
print("SWING max |alpha| %.2f |beta| %.2f |twist| %.2f deg; last 60f: %.2f %.2f %.2f" % (
    abs(ka).max(), abs(kb).max(), abs(kp).max(), abs(ka[-60:]).max(), abs(kb[-60:]).max(), abs(kp[-60:]).max()))

def bake(ob, path, idx, vals):
    if not ob.animation_data:
        ob.animation_data_create()
    if not ob.animation_data.action:
        ob.animation_data.action = bpy.data.actions.new(ob.name + "_Action")
    fc = ob.animation_data.action.fcurves.new(path, index=idx, action_group="Swing")
    fc.keyframe_points.add(len(vals))
    co_ = np.empty(len(vals) * 2); co_[0::2] = np.arange(F0, F0 + len(vals)); co_[1::2] = vals
    fc.keyframe_points.foreach_set("co", co_)
    fc.keyframe_points.foreach_set("interpolation", [bpy.types.Keyframe.bl_rna.properties["interpolation"].enum_items["LINEAR"].value] * len(vals))
    fc.update()
bake(piv, "rotation_euler", 0, keys_a)
bake(piv, "rotation_euler", 1, keys_b)
bake(drop_e, "rotation_euler", 2, keys_p)
dc["swing_info"] = "baked pendulum: about Hang_Pivot (rope tangent point on drum), twist on Hang_Drop"

# ---------------- camera, lights, world, render ----------------
cam = O["Camera"]; cam.data.lens = 50; cam.data.sensor_width = 36; cam.data.sensor_fit = "AUTO"
cam.data.clip_end = 100
cam.location = (2.6, -8.3, 0.55);
tgt = Vector((0.05, -0.1, -1.30))
cam.rotation_euler = (tgt - cam.location).to_track_quat("-Z", "Y").to_euler()
sc.camera = cam

def light(name, kind, loc, rot, energy, **kw):
    ld = bpy.data.lights.new(name, kind); ld.energy = energy
    for k, v in kw.items():
        setattr(ld, k, v)
    ob = bpy.data.objects.new(name, ld); coll.objects.link(ob); ob.location = loc; ob.rotation_euler = rot
    return ob
light("Key_Sun", "SUN", (3, -3, 4), (math.radians(52), 0, math.radians(32)), 2.2, angle=math.radians(2.5))
light("Rim_Sun", "SUN", (-3, 3, 4), (math.radians(-60), 0, math.radians(-25)), 2.0, angle=math.radians(4))
light("Fill_Area", "AREA", (-3.5, -5.5, -0.5), (math.radians(80), 0, math.radians(-35)), 450.0, size=4.0)
w = sc.world
if w and w.use_nodes:
    bg = w.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value = (0.05, 0.05, 0.055, 1); bg.inputs["Strength"].default_value = 1.0

sc.render.resolution_x = 1080; sc.render.resolution_y = 1920; sc.render.resolution_percentage = 100
sc.render.film_transparent = True
sc.frame_set(F0)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("SAVED", OUT)
