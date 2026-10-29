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
def palm_sec(u):
    w = -0.006 - 0.009 * u; d = 0.0025 - 0.002 * u - 0.0025 * math.sin(math.pi * u) * 0.0  # centre line
    z = 0.4965 - 0.0475 * u
    C = HL(w, d, z) - DD * 0.0020 * u * u          # gentle curl toward the palm side
    hw = 0.0160 + 0.0058 * (u ** 0.85); ht = 0.0098 - 0.0024 * u
    return C, hw, ht
def palm_axis(u):
    a, _, _ = palm_sec(max(0.0, u - 0.02)); b, _, _ = palm_sec(min(1.0, u + 0.02)); return (b - a).normalized()
def palm_ring(u, grow=0.0, e=3.2, n=48, a0=0.0, a1=2 * math.pi, closed=True):
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
def shell2(u0, u1, a0, a1, grow, thick, mi=0, rim=2, nu=26, nv=24):
    bm = bmesh.new(); VV = []
    for i in range(nu + 1):
        u = u0 + (u1 - u0) * i / nu
        VV.append([bm.verts.new(p) for p in palm_ring(u, grow, n=nv, a0=a0, a1=a1, closed=False)])
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
shell2(0.05, 0.70, R(28), R(152), 0.0012, 0.0014)            # back-of-hand plate
shell2(0.72, 1.00, R(22), R(158), 0.0014, 0.0014)            # knuckle plate
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
    P1r.append(ring_pts_se(C1, Xa1, Ya1, hw1 - 0.0004, ht1 - 0.0004, 3.2, 1, a, a, closed=False)[0])
NR = 36; jrows = []
for i in range(NR + 1):
    f = i / NR; fs = f * f * (3 - 2 * f)
    pts = [P0r[k].lerp(P1r[k], fs) for k in range(NJ)]
    c = sum(pts, V()) / NJ
    rib = 0.0
    if 0.12 < f < 0.90:
        q = (f - 0.12) / 0.78; rib = 0.5 + 0.5 * math.cos(2 * math.pi * 4 * q)
    m = 1.0 - 0.07 * math.sin(math.pi * f) + 0.035 * rib * math.sin(math.pi * f)
    jrows.append([c + (p - c) * m for p in pts])
HAND.add_bm(loft_bm(jrows), Matrix(), 1)
# thin gold seam where the joint meets the palm, steel bearing ring in the middle
for f_, rad, mi in ((0.985, 0.0007, 2), (0.50, 0.0006, 4)):
    i = int(f_ * NR); pts = jrows[i]; c = sum(pts, V()) / NJ
    pts = [c + (p - c) * 1.0 for p in pts]
    tube_obj("Robo_WristSeam_%d" % mi, [p + (p - c).normalized() * 0.0004 for p in pts], rad, M_GOLD if mi == 2 else M_STEEL, closed=True)

# ---- fingers: slim, tapering, anatomical phalanges, dorsal plates, dark joints
TIPS = {}
def rot(v, ax, deg): return (Matrix.Rotation(math.radians(deg), 3, ax) @ v).normalized()
def phalanx(a, b, s, ax, w0, w1, last):
    dors = s.cross(ax).normalized()
    L = (b - a).length
    jr = w0 * 0.40
    # dark joint: axle + rounded knuckle
    HAND.add_bm(bm_cyl(jr, w0 * 0.98, 20, bev=0.0003), frame(a, ax, s), 5)
    HAND.add_bm(bm_sphere(jr * 1.02, 16, 10), Matrix.Translation(a), 1)
    # gunmetal inner link (palm side visible)
    HAND.add_bm(loft_bm([ring_pts_se(a.lerp(b, f) - dors * w0 * 0.06, ax, dors, w0 * 0.30, w0 * 0.27, 2.0, 14) for f in (0.0, 1.0)]), Matrix(), 1)
    # ivory dorsal cover: tapered, rounded ends; distal one closes over the tip
    g0 = jr * 0.95; g1 = (jr * 0.55) if not last else -w1 * 0.05
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
    HAND.add_bm(bm_sphere(0.00068, 12, 8), Matrix.Translation(a + dors * (jr + 0.00035)), 3)

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
    ("Index", -0.74, 0.0010, -4.0, (0.0235, 0.0138, 0.0098), (33, 62, 34), 0.0094),
    ("Middle", -0.25, -0.0012, -1.0, (0.0262, 0.0152, 0.0105), (36, 66, 35), 0.0098),
    ("Ring", 0.25, -0.0002, 2.5, (0.0245, 0.0145, 0.0100), (38, 66, 34), 0.0092),
    ("Pinky", 0.72, 0.0030, 6.5, (0.0192, 0.0110, 0.0088), (40, 64, 32), 0.0080),
]
sK, XK, YK = frame_xy(sK, XW)
if YK.dot(DD) < 0: YK = -YK
for nm, fw, dz, spr, lens, flex, w in FING:
    base = CK + XK * (fw * hwK) + YK * (htK * 0.15) + sK * (-0.0030 - dz)
    s0 = rot(sK, YK, -spr)      # spread around the dorsal axis (index toward -w, pinky toward +w)
    if s0.dot(XK) * spr < 0: s0 = rot(sK, YK, spr)
    finger(nm, base, s0, -YK, lens, flex, w)
    # MCP glow dot on the knuckle plate
    HAND.add_bm(bm_sphere(0.00075, 12, 8), Matrix.Translation(CK + XK * (fw * hwK) + YK * (htK + 0.0030) + sK * (-0.004)), 3)
# thumb: from the palm side (thenar), index edge, at a natural down/forward angle, curling toward the fingers
Cb, hwb, htb = palm_sec(0.22); sb = palm_axis(0.22); sb, Xb, Yb = frame_xy(sb, XW)
if Yb.dot(DD) < 0: Yb = -Yb
tb = Cb - Xb * (hwb * 0.82) - Yb * (htb * 0.45)
HAND.add_bm(bm_sphere(0.0058, 18, 12), Matrix.Translation(tb), 1)
ts0 = (sb * 0.86 - Xb * 0.30 - Yb * 0.40).normalized()
finger("Thumb", tb, ts0, (Xb * 0.55 - Yb * 0.45).normalized(), (0.0200, 0.0170, 0.0135), (8, 16, 20), 0.0102, 0.82)
log("hand done; tips", {k: tuple(round(c, 3) for c in v) for k, v in TIPS.items()})

for acc in (MECH, EMITTER, HAND):
    acc.build(40)
