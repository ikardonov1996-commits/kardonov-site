# python3 cmp6.py STAGE6.png OUT.jpg : stage5 final (downscaled) | stage6 | alpha overlay (red=only5, cyan=only6) | crops x2 + stats
import sys, numpy as np
from PIL import Image, ImageDraw, ImageFont
S = "/tmp/claude-0/-home-user-kardonov-site/cb30cd45-1b88-5b9b-b3ff-480343f6cfce/scratchpad"
p6, out = sys.argv[1], sys.argv[2]
i6 = Image.open(p6).convert("RGBA"); W, H = i6.size
i5 = Image.open(S + "/out/stages_light/final/stage_5.png").convert("RGBA").resize((W, H), Image.LANCZOS)
BG = (15, 15, 18, 255)
def onbg(im): b = Image.new("RGBA", im.size, BG); b.alpha_composite(im); return b.convert("RGB")
a5 = np.asarray(i5)[..., 3] > 128; a6 = np.asarray(i6)[..., 3] > 128
ov = np.zeros((H, W, 3), np.uint8); both = a5 & a6
ov[both] = (110, 110, 110); ov[a5 & ~a6] = (255, 40, 40); ov[a6 & ~a5] = (40, 220, 255)
# pedestal/floor-area & left/right split stats
cols = np.where(a5 | a6)
print("alpha: px only5 %d only6 %d both %d" % ((a5 & ~a6).sum(), (a6 & ~a5).sum(), both.sum()))
for name, (y0, y1) in (("head", (0, int(H*.3))), ("torso", (int(H*.3), int(H*.55))), ("legs", (int(H*.55), int(H*.82))), ("pedestal", (int(H*.82), H))):
    x = a5[y0:y1] ^ a6[y0:y1]
    print(f"  {name}: xor px {x.sum()}  (x range of xor: {np.where(x.any(0))[0].min() if x.any() else '-'}..{np.where(x.any(0))[0].max() if x.any() else '-'})")
# marble stats on stage6: exclude arm (bluish/dark-metal pixels) roughly via saturation/hue
a = np.asarray(i6).astype(float); m = a[..., 3] > 250; rgb = a[..., :3]
mx = rgb.max(2); mn = rgb.min(2); sat = (mx - mn) / np.maximum(mx, 1)
warm = m & (rgb[..., 0] >= rgb[..., 2])      # marble/headband (warm) vs titanium/neon (cool)
blue = m & (rgb[..., 2] > rgb[..., 0] + 25) & (sat > .25)
print("stage6: max on warm px %.0f  >235 %.3f%%  p99.5 %.0f | blue px %.2f%% of statue" % (mx[warm].max(), 100*(mx[warm] > 235).mean(), np.percentile(mx[warm], 99.5), 100*blue.sum()/m.sum()))
a5f = np.asarray(i5).astype(float); m5 = a5f[..., 3] > 250; mx5 = a5f[..., :3].max(2)
print("stage5: max %.0f >235 %.3f%% p99.5 %.0f" % (mx5[m5].max(), 100*(mx5[m5] > 235).mean(), np.percentile(mx5[m5], 99.5)))
tiles = [onbg(i5), onbg(i6), Image.fromarray(ov)]
canvas = Image.new("RGB", (W * 3, H), (15, 15, 18))
for k, t in enumerate(tiles): canvas.paste(t, (k * W, 0))
canvas.save(out, quality=90)
# crops (head, arm) from stage6 & stage5 at 2x
def crop(im, box, s=2): x0, y0, x1, y1 = [int(v) for v in (box[0]*W, box[1]*H, box[2]*W, box[3]*H)]; c = im.crop((x0, y0, x1, y1)); return c.resize((c.width*s, c.height*s), Image.LANCZOS)
cs = [crop(onbg(i5), (.33, .05, .62, .32)), crop(onbg(i6), (.33, .05, .62, .32)), crop(onbg(i5), (.25, .25, .55, .62)), crop(onbg(i6), (.25, .25, .55, .62))]
Wc = sum(c.width for c in cs); Hc = max(c.height for c in cs); cc = Image.new("RGB", (Wc, Hc), (15, 15, 18)); x = 0
for c in cs: cc.paste(c, (x, 0)); x += c.width
cc.save(out.replace(".jpg", "_crops.jpg"), quality=90)
