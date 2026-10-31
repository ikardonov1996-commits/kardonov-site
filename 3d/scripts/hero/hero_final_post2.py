# Stitch final/prefinal strips, build brand glow layers + #0f0f12 preview, seam check, measurements.
#   python3 hero_final_post.py OUTDIR 'E=8:0-4+16:10-15,A=6:0-5'   env: OV=24 SHEET=path TITLE=...
import sys, os, json, colorsys, numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hero_post as HP
OUT = sys.argv[1]; JOBS = [(j.split("=")[0], j.split("=")[1] if "=" in j else "") for j in sys.argv[2].split(",")]   # "E=8:0-4+16:10-15,A=6:0-5"
OV = int(os.environ.get("OV", "24")); SHEET = os.environ.get("SHEET")
BL = np.array([0x77, 0xD9, 0xFF], np.float32) / 255; CH = np.array([0xFC, 0xCB, 0x84], np.float32) / 255
def pieces_of(spec):
    """'8:0-4+16:10-15' -> [(i, n), ...]"""
    out = []
    for part in spec.split("+"):
        n, rng = part.split(":"); a, b = [int(x) for x in rng.split("-")]; out += [(i, int(n)) for i in range(a, b + 1)]
    return out
def stitch(shot, spec):
    import glob, re
    ims = []
    if spec:
        for i, n in pieces_of(spec):
            im = np.asarray(Image.open(f"{OUT}/strips/{shot}_s{i}of{n}.png").convert("RGBA")).astype(np.float64) / 255
            H = im.shape[0]; ims.append((round(i * H / n), round((i + 1) * H / n), im))
    for f in glob.glob(f"{OUT}/strips/{shot}_r*-*.png"):
        a, b = [int(v) for v in re.findall(r"_r(\d+)-(\d+)\.png$", f)[0]]
        ims.append((a, b, np.asarray(Image.open(f).convert("RGBA")).astype(np.float64) / 255))
    ims.sort(key=lambda t: t[0]); H = ims[0][2].shape[0]
    assert ims[0][0] == 0 and ims[-1][1] == H and all(ims[k][1] == ims[k + 1][0] for k in range(len(ims) - 1)), "strip gap"
    acc = np.zeros_like(ims[0][2]); wsum = np.zeros((H, 1, 1)); r = np.arange(H)[:, None, None].astype(float)
    for k, (c0, c1, im) in enumerate(ims):
        w = np.ones_like(r)
        if k > 0: w = np.where(r < c0 - OV, 0, np.where(r < c0 + OV, (r - (c0 - OV) + .5) / (2 * OV), w))
        if k < len(ims) - 1: w = w * np.where(r >= c1 + OV, 0, np.where(r >= c1 - OV, 1 - (r - (c1 - OV) + .5) / (2 * OV), 1))
        pm = im.copy(); pm[..., :3] *= pm[..., 3:4]; acc += pm * w; wsum += w
    acc /= np.maximum(wsum, 1e-9); a = acc[..., 3:4]; rgb = np.where(a > 1e-6, acc[..., :3] / np.maximum(a, 1e-6), 0)
    return np.concatenate([rgb, a], 2), [c0 for c0, _, _ in ims[1:]]
def seam_check(im, seams):
    a = im[..., 3] > 0.5; lum = im[..., :3].max(2); res = []
    for b in seams:
        m = a[b] & a[b - 1]
        if m.sum() < 20: res.append(0.0); continue
        d0 = np.abs(lum[b] - lum[b - 1])[m].mean()
        ref = np.mean([np.abs(lum[y] - lum[y - 1])[a[y] & a[y - 1]].mean() for y in list(range(b - 12, b - 3)) + list(range(b + 4, b + 13)) if (a[y] & a[y - 1]).sum() > 20])
        res.append(d0 / max(ref, 1e-6))
    return res
def glow_layer(shot, kind, col, size):
    g = np.asarray(Image.open(f"{OUT}/{shot}_glowraw_{kind}.png")).astype(np.float64)
    g = g / (65535 if g.max() > 255 else 255); a = g.max(2) if g.ndim == 3 else g
    A = Image.fromarray((np.clip(a, 0, 1) * 65535).astype(np.uint16)).resize(size, Image.BICUBIC)
    a = np.asarray(A).astype(np.float64) / 65535
    rgba = np.concatenate([np.broadcast_to(col, a.shape + (3,)), a[..., None]], 2)
    Image.fromarray((rgba * 255 + .5).astype(np.uint8), "RGBA").save(f"{OUT}/{shot}_glow_{kind}.png"); return a
def measure(shot, im):
    H, W = im.shape[:2]; a = im[..., 3] > .8; mx = im[..., :3].max(2) * 255; rgb = im[..., :3]
    pr = json.load(open(f"{OUT}/{shot}_final_probe.json")); sx = W / int(os.environ.get(f"PROBE_W_{shot}", W))
    x0, y0, x1, y1 = [int(round(v * sx)) for v in (pr["face_tl"]["px"], pr["face_tl"]["py"], pr["face_br"]["px"], pr["face_br"]["py"])]
    f = mx[y0:y1, x0:x1][a[y0:y1, x0:x1]]
    hum = a.copy(); hum[:, :int(W * .55)] = False; hum[:int(H * .25)] = False
    arm = a.copy(); arm[:, :int(W * .6)] = False; arm[:int(H * .3)] = False; arm[int(H * .85):] = False
    ch = []
    for lo, hi in ((100, 200), (200, 256)):
        q = hum & (mx >= lo) & (mx < hi); h, s, v = colorsys.rgb_to_hsv(*[rgb[..., i][q].mean() for i in range(3)]); ch.append(f"h{h*360:.0f} s{s:.2f}")
    deep = hum & (mx < 90); r, b = rgb[..., 0] * 255, rgb[..., 2] * 255
    return (f"face max {f.max():.0f} (>235: {100*np.mean(f>235):.2f}%) | human arm max {mx[arm].max():.0f} | clipped >=250 on statue "
            f"{100*np.mean(mx[a]>=250):.2f}% | champagne lit marble mid {ch[0]}, hi {ch[1]} | blue in deep shadows (human half) {100*np.mean((b>r+3)[deep]):.1f}%")
lines = {}; prev = {}
for shot, n in JOBS:
    im, seams = stitch(shot, n); H, W = im.shape[:2]
    Image.fromarray((np.clip(im, 0, 1) * 255 + .5).astype(np.uint8), "RGBA").save(f"{OUT}/{shot}_beauty.png")
    ab = glow_layer(shot, "blue", BL, (W, H)); ac = glow_layer(shot, "champ", CH, (W, H))
    cx, cy, rr = HP.HEAD[shot]; yy, xx = np.mgrid[0:H, 0:W]; d = np.sqrt(((xx / W - cx) * W / H) ** 2 + (yy / H - cy) ** 2) / rr
    bg = np.array([15, 15, 18]) / 255 + (np.clip(1 - d, 0, 1) ** 2 * 0.022)[..., None] * np.array([1.0, .95, .9])
    base = im[..., :3] * im[..., 3:4] + bg * (1 - im[..., 3:4])
    out = 1 - (1 - base) * (1 - BL * ab[..., None]) * (1 - CH * ac[..., None])
    pv = Image.fromarray((np.clip(out, 0, 1) * 255 + .5).astype(np.uint8)); pv.save(f"{OUT}/{shot}_preview.jpg", quality=95)
    sq = seam_check(im, seams); m = measure(shot, im)
    lines[shot] = f"{shot}: {W}x{H} | {m} | seam ratio (1 = invisible) {' '.join(f'{x:.2f}' for x in sq)}"
    prev[shot] = pv; print(lines[shot])
if SHEET:
    F = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16); FB = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
    Hs = 1000; tiles = [(s, p.resize((int(p.width * Hs / p.height), Hs), Image.LANCZOS)) for s, p in prev.items()]
    Wt = sum(t.width + 16 for _, t in tiles) + 16
    Sh = Image.new("RGB", (max(Wt, 1500), Hs + 90 + 22 * len(lines) * 2), (15, 15, 18)); d = ImageDraw.Draw(Sh)
    d.text((16, 12), os.environ.get("TITLE", "Pre-final draft"), fill=(240, 240, 245), font=FB); x = 16
    for s, t in tiles: Sh.paste(t, (x, 50)); x += t.width + 16
    y = Hs + 62
    for s, l in lines.items():
        for part in (l[:l.index("| champagne")], "      " + l[l.index("| champagne") + 2:]): d.text((16, y), part, fill=(220, 215, 200), font=F); y += 22
    Sh.save(SHEET, quality=93); print("sheet", SHEET)
