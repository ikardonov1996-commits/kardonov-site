# strip of stills on #0f0f12 with labels + stats. usage: python3 strip.py OUT.jpg TITLE "label1=path1" ...
import sys, numpy as np
from PIL import Image, ImageDraw, ImageFont
out, title, items = sys.argv[1], sys.argv[2], sys.argv[3:]
BG = (15, 15, 18); W = 540; H = 720
try: F = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18); Fs = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 13)
except Exception: F = Fs = ImageFont.load_default()
canvas = Image.new("RGB", (W * len(items), H + 110), BG); d = ImageDraw.Draw(canvas)
d.text((12, 8), title, fill=(230, 230, 230), font=F)
for j, it in enumerate(items):
    lab, p = it.split("=", 1)
    im = Image.open(p).convert("RGBA").resize((W, H), Image.LANCZOS)
    tile = Image.new("RGBA", (W, H), BG + (255,)); tile.alpha_composite(im); canvas.paste(tile.convert("RGB"), (j * W, 40))
    a = np.asarray(im).astype(float); m = a[..., 3] > 250; rgb = a[..., :3][m]
    L = rgb.max(1); lum = rgb @ [0.2126, 0.7152, 0.0722]
    hsv = np.asarray(Image.fromarray(a[..., :3].astype(np.uint8)).convert("HSV")).astype(float)[m]
    lit = lum > np.percentile(lum, 70)
    blue = ((hsv[:, 0] > 120) & (hsv[:, 0] < 170) & (hsv[:, 1] > 50)).mean() * 100
    st = (f"max {L.max():.0f}  p99.5 {np.percentile(L, 99.5):.0f}  >=245 {100*(L>=245).mean():.2f}%  "
          f"black<12 {100*(lum<12).mean():.1f}%\nlit h{hsv[lit,0].mean()*360/255:.0f} s{hsv[lit,1].mean()/255:.2f}  "
          f"mid lum {np.median(lum):.0f}  blue px {blue:.1f}%")
    d.text((j * W + 12, 46), lab, fill=(232, 196, 140), font=F)
    d.text((j * W + 12, H + 46), st, fill=(190, 190, 190), font=Fs)
    print(lab, st.replace("\n", " | "))
canvas.save(out, quality=90)
