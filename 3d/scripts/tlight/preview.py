# usage: python3 preview.py dir [names...]  -> dir/_prev.jpg (beauty on #0f0f12) + stats
import sys, os, numpy as np
from PIL import Image
d = sys.argv[1]; names = sys.argv[2:] or ["hammer_site", "chisel_site"]
BG = np.array([15, 15, 18], np.float32)
tiles = []
for n in names:
    p = f"{d}/r_{n}.png"
    if not os.path.exists(p): continue
    im = np.asarray(Image.open(p).convert("RGBA")).astype(np.float32)
    a = im[..., 3:4] / 255; rgb = im[..., :3]
    comp = rgb * a + BG * (1 - a)
    m = im[..., 3] > 250; L = rgb.max(axis=2)[m]; Y = (rgb[..., :3] @ [0.2126, 0.7152, 0.0722])[m]
    print(f"{n}: maxch p50 {np.percentile(L,50):.0f} p99 {np.percentile(L,99):.0f} p99.9 {np.percentile(L,99.9):.0f} max {L.max():.0f} | >235 {100*(L>235).mean():.2f}% >250 {100*(L>250).mean():.2f}% | Y<20 {100*(Y<20).mean():.1f}% | meanRGB {rgb[m].mean(0).round(0)}")
    tiles.append(Image.fromarray(comp.astype(np.uint8)))
if tiles:
    h = 700; tiles = [t.resize((int(t.width * h / t.height), h), Image.LANCZOS) for t in tiles]
    W = sum(t.width for t in tiles); c = Image.new("RGB", (W, h), (15, 15, 18)); x = 0
    for t in tiles: c.paste(t, (x, 0)); x += t.width
    c.save(f"{d}/_prev.jpg", quality=90)
