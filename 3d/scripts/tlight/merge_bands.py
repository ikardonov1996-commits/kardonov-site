# merge band renders (BORDER) into one PNG: out = band pixels by row ranges. usage: merge_bands.py OUT part0.png:y0,y1 part1.png:y0,y1
import sys, numpy as np; from PIL import Image
out = sys.argv[1]; res = None
for a in sys.argv[2:]:
    p, r = a.split(":"); y0, y1 = (float(v) for v in r.split(","))
    im = np.asarray(Image.open(p).convert("RGBA")); H = im.shape[0]
    if res is None: res = np.zeros_like(im)
    top, bot = int(round(H * (1 - y1))), int(round(H * (1 - y0)))     # border y is from the bottom
    res[top:bot] = im[top:bot]
Image.fromarray(res).save(out); print("merged", out)
