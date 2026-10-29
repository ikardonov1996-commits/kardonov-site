# ------------------------------------------------------------------ 6. headband (round 3): sampled from the head surface
log("headband")
HC = V((-0.031, -0.002, 0.0)); FACE = V((0.81, -0.59, 0)).normalized(); fa = math.atan2(FACE.y, FACE.x)
NB = 360; BH = 0.0095; BT = 0.0026; OFF = 0.0012
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
R60 = np.percentile(RS, 60, axis=1)
RLO = np.percentile(RS[:, :3], 50, axis=1)          # lower half (forehead skin at the front)
# slope dr/dh from a line fit, clamped (top edge leans in following the skull, never flares out)
hc = HS - HS.mean(); SL = (RS - RS.mean(1, keepdims=True)) @ hc / (hc @ hc)
SL = np.clip(circ_smooth(np.clip(SL, -0.6, 0.2), 40), -0.40, 0.0)
front = np.cos(TH - fa) > math.cos(math.radians(40))
RB = np.where(front, np.minimum(R60, RLO + 0.0015), R60)
RB = circ_smooth(RB, 50)
RB = np.maximum(RB, circ_smooth(RLO, 50) - 0.0004)      # never sink into smooth skin
log("band radius", RB.min(), RB.max(), "slope", SL.min(), SL.max())

def bpoint(th, h, depth):
    i = ((th + math.pi) / (2 * math.pi) * NB - 0.5) % NB
    r = float(np.interp(i, np.arange(NB + 1), np.append(RB, RB[0])))
    sl = float(np.interp(i, np.arange(NB + 1), np.append(SL, SL[0])))
    d = V((math.cos(th), math.sin(th), 0))
    return HC + d * (r + OFF + sl * h + depth) + V((0, 0, zband(th) + h)), (d - Z * sl).normalized()

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

NEURO = Acc("Neuro_Modules", [M_NGOLD, M_GUN, M_LENS])
NGLOW = Acc("Neuro_Modules_Glow", [M_RING])
for nm, off, rr in (("Front", 0.0, 0.0105), ("TempleL", math.radians(62), 0.0082),
                    ("TempleR", math.radians(-62), 0.0082), ("Back", math.pi, 0.0092)):
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
