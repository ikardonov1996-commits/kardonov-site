# composite draft preview: back + block_rope + front on #0f0f12 at descent 0 (top) and 1 (lowered)
# usage: python3 composite.py LAYER_DIR PCT OUT.jpg [CROP_OUT.jpg]
import sys, json
from PIL import Image, ImageDraw
d, pct, outp = sys.argv[1], int(sys.argv[2]) / 100, sys.argv[3]
J = json.load(open(d + "/layers.json")); L = J["layers"]; W, H = J["canvas"]["w"], J["canvas"]["h"]
cw, ch = round(W * pct), round(H * pct)
def im(n): return Image.open(f"{d}/{n}.png").convert("RGBA")
def pos(n): r = L[n]; return round(r["x"] * pct), round(r["y"] * pct)
def frame(descent, i=0):
    c = Image.new("RGBA", (cw, ch), (15, 15, 18, 255))
    c.alpha_composite(im("windlass_back_%02d" % i), pos("windlass_back_%02d" % i))
    b = im("block_rope"); bx, by = pos("block_rope")
    dy = round((1 - descent) * J["drop_total_px"] * pct); by -= dy
    clip = round(J["clip_block_layer_above_y_px"] * pct)
    if clip > by: b = b.crop((0, clip - by, b.width, b.height)); by = clip
    c.alpha_composite(b, (bx, by))
    c.alpha_composite(im("windlass_front_%02d" % i), pos("windlass_front_%02d" % i))
    return c
A, B = frame(0.0), frame(1.0)
gap = 20; out = Image.new("RGB", (cw * 2 + gap, ch), (15, 15, 18)); out.paste(A, (0, 0)); out.paste(B, (cw + gap, 0))
dr = ImageDraw.Draw(out); dr.text((10, 10), "descent 0 (top)", fill=(200, 200, 200)); dr.text((cw + gap + 10, 10), "descent 1 (lowered)", fill=(200, 200, 200))
out.save(outp, quality=92)
if len(sys.argv) > 4:
    r = L["windlass_back_00"]; x0, y0 = round(r["x"] * pct), round(r["y"] * pct)
    A.crop((x0, y0, x0 + round(r["w"] * pct), y0 + round(r["h"] * pct) + round(0.25 * ch))).convert("RGB").save(sys.argv[4], quality=94)
# stats: max luminance of non-bg pixels
import numpy as np
a = np.asarray(A.convert("RGB")).astype(int); print("max channel", a.max(), "p99.9", np.percentile(a.max(2), 99.9))
