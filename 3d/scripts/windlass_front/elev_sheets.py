import sys, json, numpy as np
from PIL import Image, ImageDraw
D, D5, pct = sys.argv[1], sys.argv[2], 0.30
BG = (15, 15, 18, 255)
def frame(d, descent, i):
    J = json.load(open(d + "/layers.json")); L = J["layers"]; cw, ch = round(3200 * pct), round(8192 * pct)
    c = Image.new("RGBA", (cw, ch), BG)
    P = lambda n: (round(L[n]["x"] * pct), round(L[n]["y"] * pct))
    c.alpha_composite(Image.open(f"{d}/windlass_back_{i:02d}.png").convert("RGBA"), P(f"windlass_back_{i:02d}"))
    b = Image.open(d + "/block_rope.png").convert("RGBA"); bx, by = P("block_rope")
    by -= round((1 - descent) * J["drop_total_px"] * pct); clip = round(J["clip_block_layer_above_y_px"] * pct)
    if clip > by: b = b.crop((0, clip - by, b.width, b.height)); by = clip
    c.alpha_composite(b, (bx, by))
    c.alpha_composite(Image.open(f"{d}/windlass_front_{i:02d}.png").convert("RGBA"), P(f"windlass_front_{i:02d}"))
    return c, J
def crop_w(c, J, extra=0.62):      # windlass + top block, same window size for both versions
    r = J["layers"]["windlass_back_00"]; x0, y0 = round(r["x"] * pct), round(r["y"] * pct)
    return c.crop((x0, y0 - 10, x0 + round(r["w"] * pct), y0 + round(r["h"] * pct * 1.0) + round(extra * 1000 * pct * 1.3)))
def label(im, t):
    im = im.convert("RGB"); ImageDraw.Draw(im).text((8, 6), t, fill=(220, 200, 160)); return im
# 1) side-by-side 5 vs 13 deg (top position, crank frame 00)
a, Ja = frame(D5, 0.0, 0); b, Jb = frame(D, 0.0, 0)
A, B = label(crop_w(a, Ja), "ELEV 5 (current)"), label(crop_w(b, Jb), "ELEV 13 (raised)")
s = Image.new("RGB", (A.width + B.width + 16, max(A.height, B.height)), BG[:3]); s.paste(A, (0, 0)); s.paste(B, (A.width + 16, 0))
s.save(D + "/compare_elev5_vs_elev13.jpg", quality=93)
# 2) crank frames 00/03/06 at 13 deg (windlass crop, block at top)
ims = []
for i in (0, 3, 6):
    c, J = frame(D, 0.0, i); r = J["layers"]["windlass_back_00"]
    x0, y0 = round(r["x"] * pct), round(r["y"] * pct)
    ims.append(label(c.crop((x0, y0 - 10, x0 + round(r["w"] * pct), y0 + round(r["h"] * pct))), f"crank frame {i:02d} ({i*30} deg)"))
s = Image.new("RGB", (sum(i.width for i in ims) + 32, ims[0].height), BG[:3]); x = 0
for im in ims: s.paste(im, (x, 0)); x += im.width + 16
s.save(D + "/crank_frames_elev13.jpg", quality=93)
# zoomed crank-only strip (x2) for rotation judgement
zs = [im.crop((im.width - 200, 0, im.width, 160)).resize((400, 320), Image.LANCZOS) for im in ims]
z = Image.new("RGB", (400 * 3 + 32, 320), BG[:3])
for k, im in enumerate(zs): z.paste(im, (k * 416, 0))
z.save(D + "/crank_zoom_elev13.jpg", quality=93)
# 3) plumb / centre check on block_rope (full-res canvas coords /pct): rope centre x per row in the free span
J = Jb; L = J["layers"]["block_rope"]; al = np.asarray(Image.open(D + "/block_rope.png"))[..., 3].astype(float)
xs = []
for y in range(round(40), round(al.shape[0] * 0.70), 25):
    row = al[y]; 
    if row.sum() > 0: xs.append((L["x"] * pct + (row * np.arange(len(row))).sum() / row.sum() + 0.5) / pct)
xs = np.array(xs); print("rope centre x (canvas px) min %.1f max %.1f mean %.1f | pivot_px x %.1f | drop_total_px %.1f | swing pivot y %.1f"
      % (xs.min(), xs.max(), xs.mean(), J["pivot_px"][0], J["drop_total_px"], J["pivot_px"][1]))
