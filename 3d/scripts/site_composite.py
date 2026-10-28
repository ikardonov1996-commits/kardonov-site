# Simulate the site: windlass back layer, then the block (translated by descent, rope clipped above the
# drum line, rotated around the pivot for swing), then the windlass front layer. Writes a contact sheet.
import json, sys
from PIL import Image
d = sys.argv[1]; info = json.load(open(d + "/layers.json"))
W, H = info["canvas"]["w"], info["canvas"]["h"]; L = info["layers"]
px, py = info["pivot_px"]; drop = info["drop_total_px"]
blk = Image.open(d + "/block_rope.png").convert("RGBA")
def put(canvas, name):
    im = Image.open("%s/%s.png" % (d, name)).convert("RGBA"); r = L[name]
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); layer.paste(im, (r["x"], r["y"]))
    canvas.alpha_composite(layer)
def frame(descent, swing_deg, wi):
    c = Image.new("RGBA", (W, H), (40, 40, 44, 255))
    put(c, "windlass_back_%02d" % wi)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); b = L["block_rope"]
    lay.paste(blk, (b["x"], int(b["y"] - (1 - descent) * drop)))
    lay = lay.rotate(swing_deg, center=(px, py), resample=Image.BICUBIC)
    a = lay.split()[3]; a.paste(0, (0, 0, W, int(py)))          # rope above the drum line is hidden
    lay.putalpha(a); c.alpha_composite(lay)
    put(c, "windlass_front_%02d" % wi)
    return c.crop((0, 0, W, min(H, int(py + drop + 1.2 * info["px_per_m"] * 1.6))))
shots = [frame(0.0, 0, 0), frame(0.5, 2.5, 4), frame(1.0, -2.0, 8)]
k = 4 if W > 2000 else 3
sh = [s.resize((s.width // k, s.height // k)) for s in shots]
sheet = Image.new("RGB", (sum(s.width for s in sh), max(s.height for s in sh)), (40, 40, 44))
x = 0
for s in sh: sheet.paste(s.convert("RGB"), (x, 0)); x += s.width
sheet.save(d + "/composite_check.png"); print("OK", sheet.size)
