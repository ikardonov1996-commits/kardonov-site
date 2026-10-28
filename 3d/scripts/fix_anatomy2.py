# Anatomy fixes on the voxel-remeshed (clean, single-surface) sculpture.
#   nipples : cut out, refill with fresh mesh, shape = smooth fit of the pec + designed profile
#   bump    : same, flat profile (removes the blob above the right nipple)
#   navel   : rub the old protruding navel flat, carve a recess on the abs midline
# Everything works on a local neighbourhood only (no full-mesh scans), so each fix
# takes seconds.
# usage: blender -b -P fix_anatomy2.py -- IN.blend OUT.blend nipR,nipL,bump,navel
import bpy, bmesh, sys, time, numpy as np
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
src, dst, todo = argv[0], argv[1], argv[2].split(",")
bpy.ops.wm.open_mainfile(filepath=src)
me = bpy.data.objects["Sculpture_HiRes"].data
n = len(me.vertices)
CO = np.empty(n * 3); me.vertices.foreach_get('co', CO); CO = CO.reshape(-1, 3)
NO = np.empty(n * 3); me.vertices.foreach_get('normal', NO); NO = NO.reshape(-1, 3)
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
pl = bm.faces.layers.int.new('patch'); el = bm.edges.layers.int.new('rim'); rl = bm.verts.layers.int.new('region')

def front(x, z):
    m = (np.abs(CO[:, 0] - x) < 0.003) & (np.abs(CO[:, 2] - z) < 0.003)
    return CO[np.where(m)[0][np.argmin(CO[m, 1])]]

# profiles in local tangent coords (u horizontal, v vertical), metres
def nipple(u, v):
    d = np.hypot(u, v); return 0.0011 * np.exp(-(d / 0.0019) ** 2) + 0.00012 * np.exp(-(d / 0.0028) ** 2)
def navel(u, v):
    d = np.hypot(u / 0.0032, v / 0.0050)                                   # vertical oval
    pit = -0.0030 * np.clip(1 - d * d, 0, 1) ** 1.5
    lip = 0.00035 * np.exp(-((v - 0.0045) / 0.0016) ** 2) * np.exp(-(u / 0.004) ** 2)  # soft upper fold
    return pit + lip
def nipple_low(u, v):   # same tip, areola almost level with the skin
    d = np.hypot(u, v); return 0.0011 * np.exp(-(d / 0.0019) ** 2) + 0.00004 * np.exp(-(d / 0.0028) ** 2)
def flat(u, v): return 0 * u

class Frame:
    """Local tangent frame at p + quadratic fit of the surrounding surface."""
    def __init__(self, p, r_ring):
        d = np.linalg.norm(CO - p, axis=1)
        ring = np.where((d > r_ring[0]) & (d < r_ring[1]))[0]
        nrm = NO[ring].mean(0); nrm /= np.linalg.norm(nrm)
        t1 = np.cross(nrm, [0, 0, 1.0]); t1 /= np.linalg.norm(t1); t2 = np.cross(nrm, t1)
        if t2[2] < 0: t2 = -t2
        self.p, self.n, self.t1, self.t2 = p, nrm, t1, t2
        u, v, h = self.local(CO[ring]); keep = np.abs(h) < 0.01
        self.coef, *_ = np.linalg.lstsq(self.A(u[keep], v[keep]), h[keep], rcond=None)
    @staticmethod
    def A(u, v): return np.c_[np.ones_like(u), u, v, u * u, u * v, v * v]
    def local(self, P): q = np.atleast_2d(P) - self.p; return q @ self.t1, q @ self.t2, q @ self.n
    def tang(self, co): u, v, _ = self.local(np.array(co[:])); return u[0], v[0]
    def base(self, u, v): return (self.A(np.atleast_1d(u), np.atleast_1d(v)) @ self.coef)[0]
    def place(self, u, v, prof):
        return Vector(self.p + u * self.t1 + v * self.t2 + (self.base(u, v) + prof(u, v)) * self.n)

def tag_region(p, r, k):
    """Tag original verts near p with region id k (tags survive later edits, refs do not)."""
    for i in np.where(np.abs(CO - p).max(1) < r)[0]: bm.verts[i][rl] = k
def region_verts(k): return [v for v in bm.verts if v[rl] == k]

def smooth(verts, factor, iters=1, normal=None):
    """Laplacian smoothing of verts in numpy (bmesh.ops.smooth_vert scans the whole mesh per call)."""
    if not verts: return
    vs = list(set(verts))
    allv = list(set(vs) | {e.other_vert(v) for v in vs for e in v.link_edges})
    ix = {v: i for i, v in enumerate(allv)}
    P = np.array([v.co[:] for v in allv])
    pairs = np.array([(ix[v], ix[e.other_vert(v)]) for v in vs for e in v.link_edges])
    I = np.array([ix[v] for v in vs])
    deg = np.bincount(pairs[:, 0], minlength=len(allv))[I][:, None]
    for _ in range(iters):
        acc = np.zeros_like(P); np.add.at(acc, pairs[:, 0], P[pairs[:, 1]])
        d = acc[I] / deg - P[I]
        if normal is not None: d -= np.outer(d @ normal, normal)   # slide along the surface only
        P[I] += factor * d
    for v, i in zip(vs, I): v.co = P[i]

def relax_and_smooth(F, inner, band, prof, iters=100, seam_iters=20):
    """Tangential Laplacian relax of the new verts, re-projected onto fit+profile (numpy)."""
    inner_set = set(inner)
    verts = list(inner_set | {e.other_vert(v) for v in inner for e in v.link_edges})
    ix = {v: i for i, v in enumerate(verts)}
    P = np.array([v.co[:] for v in verts])
    pairs = np.array([(ix[v], ix[e.other_vert(v)]) for v in inner for e in v.link_edges])
    I = np.array([ix[v] for v in inner])
    deg = np.bincount(pairs[:, 0], minlength=len(verts))[I][:, None]
    for _ in range(iters):
        acc = np.zeros_like(P); np.add.at(acc, pairs[:, 0], P[pairs[:, 1]])
        q = acc[I] / deg - F.p
        u, w = q @ F.t1, q @ F.t2
        h = F.A(u, w) @ F.coef + prof(u, w)
        P[I] = F.p + np.outer(u, F.t1) + np.outer(w, F.t2) + np.outer(h, F.n)
    for v, i in zip(inner, I): v.co = P[i]
    smooth(band, 0.5, seam_iters)

def cut_and_fill(name, p, prof, r_cut, r_ring, region, seam=(0.55, 1.25, 20)):
    F = Frame(p, r_ring)
    region = [v for v in region if v.is_valid]
    def rel(v): u, w = F.tang(v.co); return np.dot(np.array(v.co[:]) - p, F.n) - F.base(u, w)
    dead = [v for v in region if np.hypot(*F.tang(v.co)) < r_cut and -0.010 < rel(v) < 0.015]
    dead_f = list({f for v in dead for f in v.link_faces})
    bmesh.ops.delete(bm, geom=dead_f, context='FACES_ONLY')
    bmesh.ops.delete(bm, geom=[v for v in dead if v.is_valid and not v.link_faces], context='VERTS')
    region = [v for v in region if v.is_valid]
    rim = list({e for v in region for e in v.link_edges if e.is_boundary})
    for e in rim: e[el] = 1
    res = bmesh.ops.triangle_fill(bm, use_beauty=True, use_dissolve=False, edges=rim)
    patch = [g for g in res['geom'] if isinstance(g, bmesh.types.BMFace)]
    for f in patch: f[pl] = 1
    def collect():   # patch faces reachable from the rim without crossing it
        seeds = {f for e in rim for f in e.link_faces if f[pl] == 1}
        out, stack = set(seeds), list(seeds)
        while stack:
            f = stack.pop()
            for e in f.edges:
                if e[el]: continue
                for g in e.link_faces:
                    if g not in out and g[pl] == 1: out.add(g); stack.append(g)
        return list(out)
    for _ in range(3):
        edges = list({e for f in patch for e in f.edges if not e[el]})
        bmesh.ops.subdivide_edges(bm, edges=edges, cuts=1, use_grid_fill=True)
        bmesh.ops.triangulate(bm, faces=collect())
        patch = collect()
    rimv = {v for e in rim for v in e.verts}
    inner = list({v for f in patch for v in f.verts if v not in rimv})
    bmesh.ops.recalc_face_normals(bm, faces=list(set(patch) | {f for v in rimv for f in v.link_faces}))
    allv = region + inner
    band = [v for v in allv if v.is_valid and r_cut * seam[0] < np.hypot(*F.tang(v.co)) < r_cut * seam[1] and abs(rel(v)) < 0.006]
    relax_and_smooth(F, inner, band, prof, seam_iters=seam[2])
    print("%s: cut %d faces, rim %d, new verts %d" % (name, len(dead_f), len(rim), len(inner)))

def smooth_carve(name, p, prof, region, shift=(0, 0, 0), r_flat=0.0075, r_blend=0.0105, r_pit=0.0065, fit=False, ring=(0.011, 0.017), depth=0.008, iters=100, trelax=0):
    F = Frame(p, ring)
    du, dv = np.dot(shift, F.t1), np.dot(shift, F.t2)
    near = [v for v in region if v.is_valid and np.dot(np.array(v.co[:]) - p, F.n) > -depth]
    core = [v for v in near if np.hypot(*F.tang(v.co)) < r_flat]
    blend = [v for v in near if np.hypot(*F.tang(v.co)) < r_blend]
    if fit:   # pull the area onto the curved fit of the surrounding surface (keeps pec curvature)
        for v in blend:
            u, w = F.tang(v.co); r = np.hypot(u, w)
            t = np.clip((r - r_flat) / (r_blend - r_flat), 0, 1); wgt = 1 - t * t * (3 - 2 * t)
            v.co = v.co.lerp(Vector(F.p + u * F.t1 + w * F.t2 + F.base(u, w) * F.n), float(wgt))
        smooth(blend, 0.3, 5)
    else:
        for _ in range(iters):         # core rubbed hard, wider blend zone gently
            smooth(core, 0.6, 4); smooth(blend, 0.3, 1)
    if trelax: smooth(blend, 0.5, trelax, normal=F.n)   # even out verts bunched by the rub
    for v in core:
        u, w = F.tang(v.co); h = prof(u - du, w - dv)
        if abs(h) > 1e-7: v.co += Vector(F.n) * float(h)
    pit = [v for v in core if np.hypot(*F.tang(v.co)) < r_pit]
    smooth(pit, 0.4, 3)
    print("%s: rubbed %d verts, carved" % (name, len(core)))

def soften_ring(name, p, region, r_in=0.0022, r_out=0.0080, iters=40):
    """Smooth an annulus around a feature (keeps the tip, removes creases / lowers the areola)."""
    F = Frame(p, (0.011, 0.017))
    ring = [v for v in region if v.is_valid and np.dot(np.array(v.co[:]) - p, F.n) > -0.02
            and r_in < np.hypot(*F.tang(v.co)) < r_out]
    outer = [v for v in ring if np.hypot(*F.tang(v.co)) > (r_in + r_out) / 2]
    smooth(ring, 0.5, iters); smooth(outer, 0.3, iters // 2)
    print("%s: softened %d verts" % (name, len(ring)))

FEATURES = {
    "nipR":  lambda: ('cut', front(-0.0800, 0.7180), nipple, 0.0105, (0.0125, 0.019)),
    "nipL":  lambda: ('cut', front(0.0427, 0.7385), nipple, 0.0105, (0.0125, 0.019)),
    "bump":  lambda: ('cut', front(-0.0900, 0.7600), flat, 0.0065, (0.0085, 0.014)),
    "navel": lambda: ('rub', front(-0.0132, 0.6300), navel, (0.0037, 0, 0)),   # shift onto abs midline x=-0.011
    # second pass on the decimated model: rub the old patch smooth, then raise the nipple
    "nipR2": lambda: ('rub', np.array([-0.0793, -0.0525, 0.7174]), nipple, (0, 0, 0), dict(r_flat=0.011, r_blend=0.016, r_pit=0.010, fit=True, ring=(0.017, 0.024))),
    "nipL2": lambda: ('rub', np.array([0.0424, -0.0545, 0.7381]), nipple, (0, 0, 0), dict(r_flat=0.011, r_blend=0.016, r_pit=0.010, fit=True, ring=(0.017, 0.024))),
    # on the clean remeshed model: rub only the long nipple away, keep the pec untouched, raise a new one
    "nipR3": lambda: ('rub', front(-0.0800, 0.7180), nipple, (0, 0, 0), dict(r_flat=0.0095, r_blend=0.0130, r_pit=0.007, depth=0.02, iters=250)),
    "nipR4": lambda: ('cut', front(-0.0800, 0.7180), nipple, 0.0080, (0.0100, 0.016), (0.6, 1.45, 80)),
    "nipR5": lambda: ('rub', front(-0.0800, 0.7180), nipple, (0, 0, 0), dict(r_flat=0.0080, r_blend=0.0110, r_pit=0.006, depth=0.02, iters=500, trelax=400)),
    "nipR4": lambda: ('cut', front(-0.0800, 0.7180), nipple, 0.0080, (0.0100, 0.016)),
    "nipL4": lambda: ('cut', front(0.0427, 0.7385), nipple_low, 0.0075, (0.0095, 0.015), (0.6, 1.45, 80)),
    "nipLsoft": lambda: ('soft', front(0.0427, 0.7385), dict(r_out=0.0095, iters=150)),
    "nipL3": lambda: ('rub', front(0.0427, 0.7385), nipple_low, (0, 0, 0), dict(r_flat=0.0048, r_blend=0.0100, r_pit=0.0045, depth=0.02, iters=60, trelax=100)),
}
jobs = [(k, FEATURES[k]()) for k in todo]
for i, (k, j) in enumerate(jobs): tag_region(j[1], 0.02, i + 1)
for i, (k, j) in enumerate(jobs):
    t = time.time(); region = region_verts(i + 1)
    if j[0] == 'soft': soften_ring(k, j[1], region, **(j[2] if len(j) > 2 else {}))
    elif j[0] == 'cut': cut_and_fill(k, j[1], j[2], j[3], j[4], region, *j[5:])
    else: smooth_carve(k, j[1], j[2], region, shift=j[3], **(j[4] if len(j) > 4 else {}))
    print("  %.1fs" % (time.time() - t), flush=True)
bm.normal_update(); bm.to_mesh(me); me.update()
me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
bpy.ops.wm.save_as_mainfile(filepath=dst, compress=True)
