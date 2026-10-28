# Raw quarried marble block that fully contains the sculpture.
# A box is chipped by many random planes (only where they keep a margin to the statue),
# remeshed, then roughened with two displacement layers. Same "Marble" material, polish=0.
# usage: blender -b IN.blend -P block.py -- OUT.blend [seed]
import bpy, bmesh, sys, numpy as np
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
out_path = argv[0]; seed = int(argv[1]) if len(argv) > 1 else 7
rng = np.random.default_rng(seed)

statue = bpy.data.objects["Sculpture_HiRes"]
me = statue.data
pts = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', pts); pts = pts.reshape(-1, 3)
pts = pts[::7] @ np.array(statue.matrix_world.to_3x3()).T + np.array(statue.matrix_world.translation)
MARGIN = 0.015                        # min distance from any cut plane to the statue
DISP = 0.006                          # displacement amplitude kept inside that margin

lo, hi = pts.min(0), pts.max(0)
size = np.array([0.50, 0.40, 1.10])
centre = np.array([(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, size[2] / 2 - 0.012])   # sunk 12 mm into the floor

old = bpy.data.objects.get("Marble_Block")
if old: bpy.data.objects.remove(old)
bm = bmesh.new()
bmesh.ops.create_cube(bm, size=1.0)
for v in bm.verts: v.co = Vector(np.array(v.co) * size + centre)

def cut(nrm, c):
    res = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=Vector(nrm * c), plane_no=Vector(nrm), clear_outer=True)
    bmesh.ops.contextual_create(bm, geom=[e for e in res['geom_cut'] if isinstance(e, bmesh.types.BMEdge)])
# --- 0) main sides slightly out of square: tilt each side by up to ~4 degrees
for axis in (0, 1):
    for sgn in (-1, 1):
        nrm = np.zeros(3); nrm[axis] = sgn
        nrm += rng.uniform(-0.07, 0.07, 3) * np.array([1, 1, 1.0]); nrm[2] = abs(nrm[2]) * 0.5; nrm /= np.linalg.norm(nrm)
        verts = np.array([v.co[:] for v in bm.verts])
        c = min((verts @ nrm).max() - 0.005, (pts @ nrm).max() + MARGIN + rng.uniform(0.02, 0.05))
        cut(nrm, c)
# --- 0b) a few deep breaks where the figure leaves room (around the head, the lower legs)
deep = 0
for _ in range(600):
    if deep >= 8: break
    d = rng.normal(size=3); d[2] = rng.choice([-0.2, 0.9]) * abs(d[2]) + rng.uniform(0.1, 0.6) * np.sign(rng.uniform(-1, 1))
    nrm = d / np.linalg.norm(d)
    if nrm[2] < -0.3: continue
    verts = np.array([v.co[:] for v in bm.verts])
    c = (verts @ nrm).max() - rng.uniform(0.05, 0.12)
    if (pts @ nrm).max() > c - MARGIN: continue
    cut(nrm, c); deep += 1
print("deep breaks:", deep)
# --- 1) planar chips: many shallow facets, biased toward edges/corners; each clears the statue
cuts = 0
for _ in range(1500):
    if cuts >= 70: break
    d = rng.normal(size=3); d[2] *= 0.6
    corner = np.sign(rng.uniform(-1, 1, 3)) * size / 2
    d = d / np.linalg.norm(d) * 0.5 + corner / np.linalg.norm(corner)
    nrm = d / np.linalg.norm(d)
    if nrm[2] < -0.3: continue                                  # bottom edges stay intact (block stands flat)
    verts = np.array([v.co[:] for v in bm.verts])
    depth = rng.uniform(0.010, 0.050)
    if nrm[2] > 0.3: depth = min(depth, 0.030)                  # no pointy apex on top
    c = (verts @ nrm).max() - depth
    if (pts @ nrm).max() > c - MARGIN: continue
    res = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=Vector(nrm * c), plane_no=Vector(nrm), clear_outer=True)
    bmesh.ops.contextual_create(bm, geom=[e for e in res['geom_cut'] if isinstance(e, bmesh.types.BMEdge)])
    cuts += 1
# the cut block is convex: rebuild it as the convex hull of what is left (guarantees a closed solid)
hull_pts = [v.co.copy() for v in bm.verts]; bm.free(); bm = bmesh.new()
for p in hull_pts: bm.verts.new(p)
bmesh.ops.convex_hull(bm, input=bm.verts[:])
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
bm.normal_update()
# --- 2) concave scallops (chisel/impact marks) along the sharp edges
spots = []
for e in bm.edges:
    if len(e.link_faces) != 2 or e.calc_face_angle(0) < 0.35: continue
    a_, b_ = np.array(e.verts[0].co), np.array(e.verts[1].co)
    out = np.array(e.link_faces[0].normal + e.link_faces[1].normal); out /= np.linalg.norm(out)
    if out[2] < -0.5: continue
    for _ in range(max(1, int(np.linalg.norm(b_ - a_) / 0.06))):
        spots.append((a_ + (b_ - a_) * rng.uniform(), out))
rng.shuffle(spots)
big = []
for f in bm.faces:
    if f.normal.z < -0.5 or f.calc_area() < 0.01: continue
    for _ in range(int(f.calc_area() / 0.03) + 1):
        w = rng.dirichlet(np.ones(len(f.verts)))
        big.append((sum((np.array(v.co) * wi for v, wi in zip(f.verts, w))), np.array(f.normal), True))
rng.shuffle(big)
mesh = bpy.data.meshes.new("Marble_Block"); bm.to_mesh(mesh); bm.free()
blk = bpy.data.objects.new("Marble_Block", mesh)
bpy.context.scene.collection.objects.link(blk)
print('after cuts polys', len(mesh.polygons))
sbm = bmesh.new(); scallops = 0
for item in big[:40] + [(p, o, False) for p, o in spots]:
    p, out, is_big = item
    if scallops >= 130: break
    if is_big: r = rng.uniform(0.06, 0.15); cen = p + out * r * rng.uniform(0.86, 0.95)   # shallow wide hollow
    else: r = rng.uniform(0.015, 0.05); cen = p + out * r * rng.uniform(0.35, 0.7)     # chisel chip on an edge
    if np.linalg.norm(pts - cen, axis=1).min() < r * 1.25 + MARGIN: continue   # squashed sphere stays clear
    tmp = bmesh.new(); bmesh.ops.create_icosphere(tmp, subdivisions=2, radius=r)
    sq = np.diag(rng.uniform(0.8, 1.25, 3))
    for v in tmp.verts: v.co = Vector(sq @ np.array(v.co) + cen)
    m_ = bpy.data.meshes.new("tmp"); tmp.to_mesh(m_); tmp.free(); sbm.from_mesh(m_); bpy.data.meshes.remove(m_)
    scallops += 1
sm = bpy.data.meshes.new("Scallops"); sbm.to_mesh(sm); sbm.free()
so = bpy.data.objects.new("Scallops", sm); bpy.context.scene.collection.objects.link(so)
bo = blk.modifiers.new("Scallops", 'BOOLEAN'); bo.operation = 'DIFFERENCE'; bo.object = so; bo.solver = 'EXACT'; bo.use_self = True; bo.use_hole_tolerant = True   # scallops overlap each other
bpy.context.view_layer.objects.active = blk; blk.select_set(True)
print('scallop polys', len(sm.polygons)); bpy.ops.object.modifier_apply(modifier=bo.name); print('after boolean polys', len(blk.data.polygons)); bpy.data.objects.remove(so)
print("chips:", cuts, "scallops:", scallops)

# --- even topology, then rough stone surface
bpy.context.view_layer.objects.active = blk; blk.select_set(True)
mesh.remesh_voxel_size = 0.004; bpy.ops.object.voxel_remesh()
def disp(name, tex_type, size_, strength):
    t = bpy.data.textures.get(name) or bpy.data.textures.new(name, tex_type)
    if tex_type == 'VORONOI': t.distance_metric = 'DISTANCE'; t.noise_intensity = 1.0
    else: t.noise_basis = 'ORIGINAL_PERLIN'
    t.noise_scale = size_
    m = blk.modifiers.new(name, 'DISPLACE'); m.texture = t; m.strength = strength; m.mid_level = 1.0   # only pushes inward
    m.texture_coords = 'GLOBAL'
disp("BlockChunks", 'VORONOI', 0.07, DISP)        # broad faceted unevenness
disp("BlockWaves", 'CLOUDS', 0.15, 0.004)       # soft undulation of the big faces
disp("BlockGrain", 'CLOUDS', 0.012, 0.0015)       # fine roughness
for m in list(blk.modifiers): bpy.ops.object.modifier_apply(modifier=m.name)
blk.data.polygons.foreach_set('use_smooth', [False] * len(blk.data.polygons))
blk.data.materials.append(bpy.data.materials["Marble"])
blk["polish"] = 0.0; blk["gold"] = 0.0

# --- verify containment: every statue sample must be inside the block, at least ~8 mm deep
from mathutils.bvhtree import BVHTree
bvh = BVHTree.FromObject(blk, bpy.context.evaluated_depsgraph_get())
inside, mind = 0, 1.0
for p in pts[::20]:
    loc, nrm, idx, dist = bvh.find_nearest(Vector(p))
    if (Vector(p) - loc).dot(nrm) < 0: inside += 1; mind = min(mind, dist)
print("statue samples inside: %d / %d, min clearance %.1f mm" % (inside, len(pts[::20]), mind * 1000))
print("block polys:", len(blk.data.polygons))
bpy.ops.wm.save_as_mainfile(filepath=out_path, compress=True)
