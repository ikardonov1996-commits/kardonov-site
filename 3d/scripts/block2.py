# Raw marble block, modelled on real quarry blocks / Michelangelo's unfinished "Prisoners":
#  - a rectangular block with big flat faces, slightly out of square
#  - a few large angular breaks at corners, each made of 2-3 planes (stepped fracture)
#  - a handful of flat wedge-shaped flake chips on some edges (sharp rims, no round bites)
#  - faces: gentle waviness + fine point-chisel roughness
# Every cut keeps MARGIN clearance to the sculpture inside.
# usage: blender -b IN.blend -P block2.py -- OUT.blend [seed]
import bpy, bmesh, sys, numpy as np
from mathutils import Vector, Matrix, noise as mnoise
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index("--") + 1:]
out_path = argv[0]; seed = int(argv[1]) if len(argv) > 1 else 11
rng = np.random.default_rng(seed)
MARGIN = 0.018                         # leaves room for face waviness + joint undulation

statue = bpy.data.objects["Sculpture_HiRes"]
pts = np.empty(len(statue.data.vertices) * 3); statue.data.vertices.foreach_get('co', pts)
pts = pts.reshape(-1, 3)[::5]
lo, hi = pts.min(0), pts.max(0)
size = np.array([0.62, 0.50, 1.18])
centre = np.array([(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, size[2] / 2 - 0.012])   # sunk 12 mm into the floor

for name in ("Marble_Block", "Block_Chips"):
    o = bpy.data.objects.get(name)
    if o: bpy.data.objects.remove(o)

bm = bmesh.new()
bmesh.ops.create_cube(bm, size=1.0)
for v in bm.verts: v.co = Vector(np.array(v.co) * size + centre)
def verts(): return np.array([v.co[:] for v in bm.verts])
def clear(nrm, c): return (pts @ nrm).max() <= c - MARGIN
def cut(nrm, c):
    res = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=Vector(nrm * c), plane_no=Vector(nrm), clear_outer=True)
    bmesh.ops.contextual_create(bm, geom=[e for e in res['geom_cut'] if isinstance(e, bmesh.types.BMEdge)])
def unit(v): return v / np.linalg.norm(v)

# 1) sides slightly out of square (<= ~2 degrees), top slightly tilted
# planes of the dressed (original) faces: everything else is a fresh fracture -> rust patina
primary = [(np.eye(3)[i] * s_, (centre + s_ * size / 2)[i] * s_) for i in range(3) for s_ in (-1, 1)]
for axis, sgn in ((0, -1), (0, 1), (1, -1), (1, 1), (2, 1)):
    nrm = np.zeros(3); nrm[axis] = sgn
    nrm = unit(nrm + rng.uniform(-0.035, 0.035, 3) * (np.arange(3) != axis))
    c = (verts() @ nrm).max() - rng.uniform(0.0, 0.012)
    if clear(nrm, c): cut(nrm, c); primary.append((nrm, c))

# 2) large angular breaks at corners: main plane + 1-2 stepped planes nearly parallel to it
corners = [np.array([sx, sy, sz]) for sx in (-1, 1) for sy in (-1, 1) for sz in (1, 1, -0.0)]
rng.shuffle(corners); breaks = 0; break_planes = []
for cdir in corners:
    if breaks >= 4: break
    for _ in range(40):
        d = cdir * np.array([1, 1, rng.uniform(0.2, 1.2)]) + rng.normal(scale=0.35, size=3)
        if cdir[2] == 0: d[2] = rng.uniform(-0.1, 0.4)        # vertical edge breaks
        nrm = unit(d)
        if nrm[2] < -0.2: continue
        c = (verts() @ nrm).max() - rng.uniform(0.05, 0.16)
        if not clear(nrm, c): continue
        cut(nrm, c); break_planes.append((nrm, c))
        for _s in range(rng.integers(1, 3)):                  # stepped fracture terraces
            n2 = unit(nrm + rng.normal(scale=0.22, size=3))
            c2 = (verts() @ n2).max() - rng.uniform(0.006, 0.02)
            if n2[2] > -0.2 and clear(n2, c2): cut(n2, c2)
        breaks += 1; break
# rebuild as a clean closed convex solid
hull = [v.co.copy() for v in bm.verts]; bm.free(); bm = bmesh.new()
for p in hull: bm.verts.new(p)
bmesh.ops.convex_hull(bm, input=bm.verts[:])
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:]); bm.normal_update()

# 3) flake chips: flat wedges on some edges (box tilted 15-35 deg into one face)
edges = []
for e in bm.edges:
    if len(e.link_faces) == 2 and e.calc_face_angle(0) > 0.6:
        n1, n2 = (np.array(f.normal) for f in e.link_faces)
        if (n1 + n2)[2] < -0.6: continue                       # not along the bottom
        edges.append((np.array(e.verts[0].co), np.array(e.verts[1].co), n1, n2))
mesh = bpy.data.meshes.new("Marble_Block"); bm.to_mesh(mesh); bm.free()
blk = bpy.data.objects.new("Marble_Block", mesh); bpy.context.scene.collection.objects.link(blk)
cbm = bmesh.new(); flakes = 0; placed = []
hubs = [(rng.integers(len(edges)), rng.uniform(0.15, 0.85)) for _ in range(7)]
for _ in range(4000):
    if flakes >= 40: break
    if rng.uniform() < 0.75:                                    # most chips gather around a few impact spots
        ei, t0 = hubs[rng.integers(len(hubs))]
        a, b, n1, n2 = edges[ei]
        tpos = t0 + rng.normal(scale=0.09 / max(np.linalg.norm(b - a), 1e-3))
        if not 0.03 < tpos < 0.97: continue
    else:
        a, b, n1, n2 = edges[rng.integers(len(edges))]; tpos = rng.uniform(0.08, 0.92)
    p = a + (b - a) * tpos
    out = unit(n1 + n2 + rng.normal(scale=0.12, size=3))          # bisect the edge: equal bite into both faces
    R = rng.uniform(0.08, 0.17); D = rng.uniform(0.005, 0.011)     # conchoidal: wide, shallow bite
    t = unit(b - a); u = unit(np.cross(out, t)); t = unit(np.cross(u, out))
    ax, ay = rng.uniform(1.6, 2.8), rng.uniform(1.0, 1.5)          # elongated along the edge
    foot = np.sqrt(2 * R * D) * ax * 1.2                           # half-length of the scar on the surface
    if any(np.linalg.norm(p - q) < 0.7 * (foot + fq) for q, fq in placed): continue   # scars never overlap -> no deep merged pits
    F = np.column_stack([t * ax, u * ay, out]) * R
    cen = p + out * (R - D)
    if np.linalg.norm(pts - cen, axis=1).min() < R * max(ax, ay) * 1.15 + MARGIN: continue
    tmp = bmesh.new(); bmesh.ops.create_icosphere(tmp, subdivisions=4, radius=1.0)
    off = Vector(rng.uniform(-50, 50, 3))
    for v in tmp.verts:                                            # irregular outline: noisy, not a circle
        k = 1.0 + 0.16 * mnoise.noise(v.co * 2.2 + off) + 0.06 * mnoise.noise(v.co * 6.0 + off)
        v.co = Vector(cen + F @ (np.array(v.co) * k))
    m_ = bpy.data.meshes.new("tmp"); tmp.to_mesh(m_); tmp.free(); cbm.from_mesh(m_); bpy.data.meshes.remove(m_)
    flakes += 1; placed.append((p, foot))
cm = bpy.data.meshes.new("Block_Chips"); cbm.to_mesh(cm); cbm.free()
co_ = bpy.data.objects.new("Block_Chips", cm); bpy.context.scene.collection.objects.link(co_)
bo = blk.modifiers.new("Chips", 'BOOLEAN'); bo.operation = 'DIFFERENCE'; bo.object = co_
bo.solver = 'EXACT'; bo.use_self = True; bo.use_hole_tolerant = True
bpy.context.view_layer.objects.active = blk; blk.select_set(True)
bpy.ops.object.modifier_apply(modifier=bo.name); bpy.data.objects.remove(co_)
print("breaks:", breaks, "flakes:", flakes, "polys:", len(blk.data.polygons))

# 4) surface: even topology, gentle waviness + fine point-chisel roughness (inward only)
blk.data.remesh_voxel_size = 0.003; bpy.ops.object.voxel_remesh()
# mark fracture surfaces: vertices farther than 2.5 mm from every dressed face plane
nv = len(blk.data.vertices); V = np.empty(nv * 3); blk.data.vertices.foreach_get('co', V); V = V.reshape(-1, 3)
dmin = np.min(np.stack([np.abs(V @ n_ - c_) for n_, c_ in primary]), axis=0)
frac = np.clip((dmin - 0.0015) / 0.003, 0, 1)
at = blk.data.attributes.new("fracture", 'FLOAT', 'POINT'); at.data.foreach_set('value', frac)
print("fracture verts: %.0f%%" % (100 * (frac > 0.5).mean()))
# old natural joints: the 1-2 largest break planes carry iron-oxide patina; other breaks are fresh
cnt = [((np.abs(V @ n_ - c_) < 0.004) & (frac > 0.5)).sum() for n_, c_ in break_planes]
order = list(np.argsort(cnt)[::-1][:2 if rng.uniform() < 0.6 else 1])
joint = np.zeros(nv)
for k in order:
    n_, c_ = break_planes[k]; joint = np.maximum(joint, ((np.abs(V @ n_ - c_) < 0.004) & (frac > 0.5)).astype(float))
ja = blk.data.attributes.new("joint", 'FLOAT', 'POINT'); ja.data.foreach_set('value', joint)
print("joint planes:", len(order), "joint verts: %.0f%%" % (100 * joint.mean()))
# worn arrises: round dressed edges with a 2-5 mm fillet that varies along the edge
D2 = np.sort(np.stack([np.abs(V @ n_ - c_) for n_, c_ in primary]), axis=0)
d2 = D2[1]                                                     # distance to the 2nd nearest dressed plane
r = 0.002 + 0.003 * (0.5 + 0.5 * np.array([mnoise.noise(Vector(p) * 12.0) for p in V]))
NV = np.empty(nv * 3); blk.data.vertices.foreach_get('normal', NV); NV = NV.reshape(-1, 3)
on = (d2 < r) & (frac < 0.5) & (D2[0] < 0.0015)
depth = np.where(on, r - np.sqrt(np.clip(r ** 2 - (r - d2) ** 2, 0, None)), 0.0)
V2 = V - NV * depth[:, None]; blk.data.vertices.foreach_set('co', V2.ravel()); blk.data.update()
print("worn edge verts:", int(on.sum()))
# old joints: undulating crack surface (not a sawn plane) + distance to the joint's rim
from mathutils.kdtree import KDTree
Jidx = np.where(joint > 0.5)[0]; Oidx = np.where(joint <= 0.5)[0]
kd = KDTree(len(Oidx))
for k, i in enumerate(Oidx): kd.insert(V2[i], k)
kd.balance()
rim = np.zeros(nv); dist_rim = np.zeros(nv)
for i in Jidx:
    _, _, d = kd.find(V2[i]); dist_rim[i] = d
rim[Jidx] = 1.0 - np.clip(dist_rim[Jidx] / 0.05, 0, 1)            # 1 at the joint's edge, 0 five cm inside
ra = blk.data.attributes.new("joint_rim", 'FLOAT', 'POINT'); ra.data.foreach_set('value', rim)
und = np.array([mnoise.noise(Vector(p) * 7.0) + 0.4 * mnoise.noise(Vector(p) * 19.0) for p in V2[Jidx]])
w_in = np.clip(dist_rim[Jidx] / 0.03, 0, 1)                       # fade to zero at the rim -> no step at the edge
V2[Jidx] -= NV[Jidx] * (0.006 * und * w_in)[:, None]
blk.data.vertices.foreach_set('co', V2.ravel()); blk.data.update()
def disp(name, ttype, size_, strength, basis='ORIGINAL_PERLIN', mid=1.0):
    t = bpy.data.textures.get(name) or bpy.data.textures.new(name, ttype)
    t.noise_basis = basis; t.noise_scale = size_
    if ttype == 'CLOUDS': t.noise_depth = 4
    m = blk.modifiers.new(name, 'DISPLACE'); m.texture = t; m.strength = strength; m.mid_level = mid; m.texture_coords = 'GLOBAL'
disp("BlockWave", 'CLOUDS', 0.20, 0.012, mid=0.5)        # hand-dressed faces wander ~ +-6 mm
for m in list(blk.modifiers): bpy.ops.object.modifier_apply(modifier=m.name)
blk.data.polygons.foreach_set('use_smooth', [True] * len(blk.data.polygons))
blk.data.materials.append(bpy.data.materials["Marble"]); blk["polish"] = 0.0; blk["gold"] = 0.0

bvh = BVHTree.FromObject(blk, bpy.context.evaluated_depsgraph_get())
inside, mind = 0, 1.0
for p in pts[::25]:
    loc_, nrm_, idx, dist = bvh.find_nearest(Vector(p))
    if (Vector(p) - loc_).dot(nrm_) < 0: inside += 1; mind = min(mind, dist)
print("statue samples inside: %d / %d, min clearance %.1f mm, polys %d" % (inside, len(pts[::25]), mind * 1000, len(blk.data.polygons)))
bpy.ops.wm.save_as_mainfile(filepath=out_path, compress=True)
