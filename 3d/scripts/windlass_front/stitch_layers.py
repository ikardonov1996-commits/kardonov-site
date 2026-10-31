# assemble strip renders into full layers. usage: python3 -I stitch_layers.py OUT_DIR   (prints MISSING n / STITCHED n)
import sys, json, os
from PIL import Image
d = sys.argv[1]; M = json.load(open(d + "/strips_manifest.json")); done = missing = 0
for name, m in M.items():
    dst = f"{d}/{name}.png"
    if os.path.exists(dst) and os.path.getsize(dst) > 0: done += 1; continue
    files = [f"{d}/strips/{s['file']}" for s in m["strips"]]
    if not all(os.path.exists(f) and os.path.getsize(f) > 0 for f in files): missing += 1; continue
    r = m["rect"]; out = Image.new("RGBA", (r["w"], r["h"]), (0, 0, 0, 0))
    for s, f in zip(m["strips"], files):
        im = Image.open(f).convert("RGBA"); a0, a1 = s["rendered"]; c0, c1 = s["core"]
        assert im.size == (r["w"], a1 - a0), (f, im.size, (r["w"], a1 - a0))
        out.paste(im.crop((0, c0 - a0, r["w"], c1 - a0)), (0, c0 - r["y"]))
    out.save(dst + ".tmp.png", optimize=False); os.replace(dst + ".tmp.png", dst); done += 1
print("STITCHED", done, "MISSING", missing)
