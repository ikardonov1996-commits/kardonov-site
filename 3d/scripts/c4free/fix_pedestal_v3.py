# C4_Freed v3: the three client-approved pedestal fixes, as a post-pass on the finished C4_Freed mesh.
# (A post-pass, not edits inside build_freed.py's pipeline: the FAST booleans there do not return faces in a stable
#  order, so a full rebuild re-seeds every chip / tool mark on the whole remnant. This pass touches only:)
#   1) the round "gnawed" trench pocket by the right foot (x .23-.27, y .06-.09, z .11-.165) -> one faceted
#      conchoidal spall (convex-hull cutter: flat facets, sharp arrises, flat-shaded);
#   2) patina attributes fracture / joint / joint_rim -> 0 on the pedestal (fade over 6 mm at its boundary);
#   3) pedestal faces: the round point pits (read as uniform bubbles) are planed off and replaced by subbia work:
#      rows of elongated, faceted strikes in diagonal parallel bands, varied spacing/length/depth (<= 3.5 mm),
#      untouched flat strips between.
# Figure (the small loose part), object transform, camera, material: untouched. Idempotent (C4["c4_pedestal_fix"]).
# usage: blender -b anim_carving.blend -P fix_pedestal_v3.py -- OUT.blend      (build_freed.py also calls apply())
import bpy, bmesh, sys, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

BASE_TOP = 0.118
def _pl(n, p):
    n = Vector(n).normalized(); return (n, n.dot(Vector(p)))
def _yfront(y0, ax=0.0, az=0.0, x0=0.0, z0=0.5): return _pl((ax, -1.0, az), (x0, y0, z0))
def _ztop(z0, ax=0.0, ay=0.0, x0=0.0, y0=0.15): return _pl((-ax, -ay, 1.0), (x0, y0, z0))
BASE_PLANES = [                                   # = the cut planes of TMP_Base in build_freed.py
    _ztop(BASE_TOP, ax=0.04, ay=-0.05, x0=0.03, y0=0.0),
    _yfront(-0.192, ax=0.05, az=0.10, z0=0.05),
    _pl((1.0, -0.06, 0.12), (0.247, 0.0, 0.05)),
    _pl((-1.0, 0.05, 0.10), (-0.170, 0.0, 0.05)),
    _pl((0.70, -0.70, 0.12), (0.225, -0.172, 0.05)),
    _pl((-0.70, -0.70, 0.10), (-0.153, -0.175, 0.05)),
    _pl((0.0, -0.60, 0.80), (0.0, -0.180, BASE_TOP)),
    _pl((0.62, -0.30, 0.73), (0.235, -0.10, BASE_TOP)),
]
NOTCH_PTS = [(0.196, 0.020, 0.196), (0.268, 0.020, 0.222), (0.318, 0.020, 0.168), (0.312, 0.020, 0.092),  # outside
             (0.236, 0.020, 0.078),
             (0.229, 0.095, 0.151), (0.257, 0.099, 0.164), (0.273, 0.093, 0.124), (0.244, 0.096, 0.107),   # small back
             (0.213, 0.064, 0.137), (0.243, 0.069, 0.190), (0.292, 0.063, 0.156), (0.262, 0.061, 0.093)]   # side breaks
PATINA = ("fracture", "joint", "joint_rim")

def h01(*a):
    h = np.zeros_like(a[0], dtype=np.int64)
    for k, x in zip((73856093, 19349663, 83492791, 2654435761), a):
        h = h ^ (x.astype(np.int64) * k)
    h = (h ^ (h >> 13)) * 1274126177; h = h ^ (h >> 16)
    return (h & 0xFFFFFF).astype(np.float64) / float(0xFFFFFF)

def subbia(U, Vv, fs, lam=0.014, depth=0.0034, cell=0.14, spread=0.12, pitch=0.032):
    """point-tool dressing on a plane: (U,Vv) in-plane coords, fs = plane id (int64 array)."""
    nv = len(U)
    sgn = np.where(h01(fs, fs, fs, 22 + 0 * fs) > 0.5, 1.0, -1.0)
    base_ang = sgn * (np.pi / 4 + (h01(fs, fs, fs, 21 + 0 * fs) - 0.5) * 0.45)     # diagonal on every face
    gi = np.floor(U / cell).astype(np.int64); gj = np.floor(Vv / cell).astype(np.int64)  # big patches: one pass each
    best = np.full(nv, 1e9); ang = np.zeros(nv); ph = np.zeros(nv); pid = np.zeros(nv)
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            ci, cj = gi + di, gj + dj
            cx = (ci + h01(ci, cj, fs, 1 + 0 * ci)) * cell; cy = (cj + h01(ci, cj, fs, 2 + 0 * ci)) * cell
            d2 = (U - cx) ** 2 + (Vv - cy) ** 2; m = d2 < best; best[m] = d2[m]
            a = base_ang + (h01(ci, cj, fs, 3 + 0 * ci) - 0.5) * 2 * spread
            ang[m] = a[m]; ph[m] = h01(ci, cj, fs, 4 + 0 * ci)[m]; pid[m] = h01(ci, cj, fs, 5 + 0 * ci)[m]
    s = U * np.cos(ang) + Vv * np.sin(ang); al = -U * np.sin(ang) + Vv * np.cos(ang)
    rid = (pid * 1e4).astype(np.int64)
    lam = lam * (0.8 + 0.4 * pid)                                                # spacing varies pass to pass
    sw = s / lam + ph * 7 + 0.18 * np.sin(al / 0.045 + pid * 6.283)            # rows not ruled-straight
    row = np.floor(sw).astype(np.int64); w = sw - row
    grp = np.floor((row + (ph * 13).astype(np.int64)) / 4.0).astype(np.int64)    # ~4 rows per pass
    on = (h01(grp, rid, fs, 23 + 0 * row) < 0.62) & (h01(row, rid, fs, 24 + 0 * row) < 0.85)
    c = 0.5 + (h01(row, rid, fs, 25 + 0 * row) - 0.5) * 0.4
    hw = 0.17 + 0.13 * h01(row, rid, fs, 26 + 0 * row)
    across = np.clip(1 - np.abs(w - c) / hw, 0, 1)                                 # V section
    plen = pitch * (0.7 + 0.6 * h01(row, rid, fs, 27 + 0 * row))
    e = al / plen + h01(row, rid, fs, 28 + 0 * row); j = np.floor(e).astype(np.int64); t = e - j
    Lf = 0.55 + 0.35 * h01(j, row, rid, 29 + 0 * row); t0 = 0.3 * Lf                # steep entry, long run-out
    along = np.where(t < t0, t / t0, np.clip((Lf - t) / (Lf - t0), 0, 1))
    hit = h01(j, row, rid, 30 + 0 * row) < 0.82
    dep = depth * (0.45 + 0.55 * h01(j, row, rid, 31 + 0 * row)) * (0.7 + 0.3 * h01(row, rid, fs, 32 + 0 * row))
    return np.minimum(dep * np.minimum(across, along) * hit * on, 0.0035)          # min of ramps -> flat facets

def _vol(me):
    b = bmesh.new(); b.from_mesh(me); v = abs(b.calc_volume(signed=True)); b.free(); return v
def _holes(me):
    b = bmesh.new(); b.from_mesh(me); n = sum(1 for e in b.edges if not e.is_manifold); b.free(); return n
def _select_only(o):
    for x in bpy.context.selected_objects: x.select_set(False)
    o.select_set(True); bpy.context.view_layer.objects.active = o

def _components(me):
    nv = len(me.vertices); ed = np.empty(len(me.edges) * 2, np.int64); me.edges.foreach_get('vertices', ed)
    a, b = ed[0::2], ed[1::2]; lab = np.arange(nv)
    while True:
        m = np.minimum(lab[a], lab[b]); old = lab.copy()
        np.minimum.at(lab, a, m); np.minimum.at(lab, b, m)
        for _ in range(8): lab = lab[lab]
        if np.array_equal(lab, old): return lab

def apply(C4, log=print):
    if C4.get("c4_pedestal_fix", 0) >= 3: log("pedestal fix already applied"); return
    sc = bpy.context.scene; me = C4.data
    lab = _components(me); ids, cnt = np.unique(lab, return_counts=True)
    assert len(ids) == 2, "expected stone + figure, got %d parts" % len(ids)
    stone_id = ids[np.argmax(cnt)]; is_st = lab == stone_id
    log("stone verts %d, figure verts %d" % (is_st.sum(), (~is_st).sum()))
    # ---- split into stone / figure objects (stone first, as in build_freed.py's join)
    def part(keep_stone, name):
        b = bmesh.new(); b.from_mesh(me); b.verts.ensure_lookup_table()
        bmesh.ops.delete(b, geom=[v for v in b.verts if bool(is_st[v.index]) != keep_stone], context='VERTS')
        m = bpy.data.meshes.new(name); b.to_mesh(m); b.free()
        o = bpy.data.objects.new(name, m); sc.collection.objects.link(o); return o
    st = part(True, "FIX_stone"); fg = part(False, "FIX_figure")
    fig_co0 = np.empty(len(fg.data.vertices) * 3); fg.data.vertices.foreach_get('co', fig_co0)
    sm = st.data; nv = len(sm.vertices)
    co = np.empty(nv * 3); sm.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
    N = np.array([n[:] for n, d in BASE_PLANES]); Dd = np.array([d for n, d in BASE_PLANES])
    S = co @ N.T - Dd                                         # signed distance to every pedestal plane (+ outside)
    order = np.argsort(-S, axis=1); k = order[:, 0]; s1 = S[np.arange(nv), k]; s2 = S[np.arange(nv), order[:, 1]]
    # ---- fix 2: patina off the pedestal
    ped = np.clip(1 - s1 / 0.006, 0, 1)
    for nm in PATINA:
        a = np.empty(nv); sm.attributes[nm].data.foreach_get('value', a)
        log("  %s on pedestal before: max %.3f, verts>0.01: %d" % (nm, (a * (ped > 0)).max(), ((a * (ped > 0)) > 0.01).sum()))
        sm.attributes[nm].data.foreach_set('value', a * (1 - ped))
    # ---- fix 3: plane off the old pits on the pedestal faces, cut subbia rows
    cand = (s1 > -0.0045) & (s1 < 0.0006)
    ed = np.empty(len(sm.edges) * 2, np.int64); sm.edges.foreach_get('vertices', ed); ea, eb = ed[0::2], ed[1::2]
    f = np.where(cand, s1, -0.012); deg = np.bincount(ea, minlength=nv) + np.bincount(eb, minlength=nv) + 1
    for _ in range(6):                                        # ~6 mm neighbourhood mean: pits ~-0.5 mm, chips deeper
        acc = f.copy(); np.add.at(acc, ea, f[eb]); np.add.at(acc, eb, f[ea]); f = acc / deg
    w_chip = np.clip((f + 0.0024) / 0.0008, 0, 1)             # chip / spall surfaces near the plane: leave them
    w_arris = np.clip((-s2 - 0.0015) / 0.0025, 0, 1)          # keep the remeshed arrises themselves
    w = np.where(cand, w_chip * w_arris, 0.0)
    n_k = N[k]
    up = np.where(np.abs(n_k[:, 2:3]) > 0.9, np.array([[1.0, 0, 0]]), np.array([[0, 0, 1.0]]))
    t1 = np.cross(up, n_k); t1 /= np.linalg.norm(t1, axis=1, keepdims=True); t2 = np.cross(n_k, t1)
    proj = co - n_k * s1[:, None]
    U = (proj * t1).sum(1); Vv = (proj * t2).sum(1)
    Dn = subbia(U, Vv, k.astype(np.int64) + 101)
    target = proj - n_k * Dn[:, None]
    co2 = co + (target - co) * w[:, None]
    sm.vertices.foreach_set('co', co2.ravel()); sm.update()
    log("  subbia: %d verts reworked (w>0), %d fully; new depth max %.4f mean(on face) %.5f; old pit depth mean %.5f"
        % ((w > 0).sum(), (w > 0.999).sum(), Dn[w > 0.999].max(), Dn[w > 0.999].mean(), -s1[w > 0.999].mean()))
    for kk in range(len(BASE_PLANES)):
        mk_ = (k == kk) & cand
        log("    plane %d: cand %d reworked %d (full %d) normal %s" % (kk, mk_.sum(), (mk_ & (w > 0)).sum(),
            (mk_ & (w > 0.999)).sum(), tuple(round(x, 2) for x in N[kk])))
    # ---- fix 1: faceted spall over the round pocket
    b = bmesh.new()
    for p in NOTCH_PTS: b.verts.new(p)
    bmesh.ops.convex_hull(b, input=b.verts[:])
    for v in [v for v in b.verts if not v.link_faces]: b.verts.remove(v)
    bmesh.ops.recalc_face_normals(b, faces=b.faces[:])
    cm = bpy.data.meshes.new("FIX_notch"); b.to_mesh(cm); b.free()
    cut = bpy.data.objects.new("FIX_notch", cm); sc.collection.objects.link(cut)
    fbvh = BVHTree.FromObject(fg, bpy.context.evaluated_depsgraph_get())
    dmin = min(fbvh.find_nearest(Vector(p))[3] for p in NOTCH_PTS)
    log("  notch cutter vol %.6f, nearest figure vertex to its corners %.3f m" % (_vol(cm), dmin))
    va, vb = _vol(sm), _vol(cm); done = False
    for solver in ('EXACT', 'FAST'):
        t = st.copy(); t.data = sm.copy(); sc.collection.objects.link(t); _select_only(t)
        mo = t.modifiers.new("B", 'BOOLEAN'); mo.operation = 'DIFFERENCE'; mo.object = cut; mo.solver = solver
        if solver == 'EXACT': mo.use_hole_tolerant = True
        bpy.ops.object.modifier_apply(modifier=mo.name)
        v = _vol(t.data); hl = _holes(t.data); ok = 1e-5 < va - v <= vb * 1.002 and hl == 0
        log("  notch DIFFERENCE %s: removed %.6f m3 (cutter %.6f) holes %d %s" % (solver, va - v, vb, hl, 'ok' if ok else 'REJECT'))
        if ok:
            st.data = t.data; bpy.data.objects.remove(t); done = True; break
        bpy.data.objects.remove(t)
    bpy.data.objects.remove(cut)
    assert done, "notch boolean failed"
    _select_only(st); bpy.ops.object.shade_smooth_by_angle(angle=0.55)   # as build_freed.py
    # ---- rejoin: stone first, then the untouched figure
    for x in bpy.context.selected_objects: x.select_set(False)
    st.select_set(True); fg.select_set(True); bpy.context.view_layer.objects.active = st
    bpy.ops.object.join()
    new = st.data; new.name = "C4_Freed_v3"; old = C4.data; C4.data = new
    new.materials.clear(); new.materials.append(old.materials[0])
    bpy.data.objects.remove(st)
    if old.users == 0: bpy.data.meshes.remove(old)
    for m_ in list(bpy.data.meshes):
        if m_.users == 0: bpy.data.meshes.remove(m_)
    nf = len(fig_co0) // 3; tail = np.empty(nf * 3);
    allco = np.empty(len(new.vertices) * 3); new.vertices.foreach_get('co', allco); tail = allco[-nf * 3:]
    log("  figure verts identical after rejoin: %s" % np.array_equal(tail, fig_co0))
    C4["c4_pedestal_fix"] = 3
    log("C4_Freed v3: %d faces, open edges %d" % (len(new.polygons), _holes(new)))

if __name__ == "__main__":
    out = sys.argv[sys.argv.index("--") + 1]
    apply(bpy.data.objects["C4_Freed"], log=lambda *a: print(*a, flush=True))
    bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
    print("FIX OK", out)
