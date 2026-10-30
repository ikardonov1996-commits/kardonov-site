# hotspot map: red = max channel > 235 on non-emitter surfaces, blue = emitters/neon-tinted (b > r+45), saved _hot.jpg
import sys, numpy as np; from PIL import Image
d = sys.argv[1]; names = sys.argv[2:] or ["hammer_site", "chisel_site"]; tiles = []
for n in names:
    im = np.asarray(Image.open(f"{d}/r_{n}.png").convert("RGBA")).astype(np.float32); rgb = im[..., :3]; a = im[..., 3] > 250
    em = (rgb[..., 2] > rgb[..., 0] + 45) & a
    mx = rgb.max(2); hot = (mx > 235) & a & ~em; vhot = (mx > 250) & a & ~em
    sur = a & ~em
    print(f"{n}: surfaces >235 {100*hot.sum()/sur.sum():.2f}%  >250 {100*vhot.sum()/sur.sum():.2f}%  p99.5 surf {np.percentile(mx[sur],99.5):.0f}  emitter px {100*em.sum()/a.sum():.1f}%")
    g = (rgb.mean(2) * 0.6).astype(np.uint8); out = np.stack([g, g, g], 2)
    out[hot] = (255, 160, 0); out[vhot] = (255, 0, 0); out[em] = (60, 120, 255)
    tiles.append(Image.fromarray(out))
W = sum(t.width for t in tiles); c = Image.new("RGB", (W, tiles[0].height)); x = 0
for t in tiles: c.paste(t, (x, 0)); x += t.width
c.save(f"{d}/_hot.jpg", quality=88)
