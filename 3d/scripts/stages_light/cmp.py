# cmp.py OUT.jpg H "label=path" ...  -> side by side on #0f0f12, each scaled to height H
import sys; from PIL import Image, ImageDraw
out, H, items = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
tiles = []
for it in items:
    lab, p = it.split("=", 1); im = Image.open(p).convert("RGBA"); im = im.resize((round(im.width * H / im.height), H), Image.LANCZOS)
    t = Image.new("RGBA", im.size, (15, 15, 18, 255)); t.alpha_composite(im); t = t.convert("RGB")
    ImageDraw.Draw(t).text((6, 4), lab, fill=(232, 196, 140)); tiles.append(t)
c = Image.new("RGB", (sum(t.width for t in tiles) + 6 * len(tiles), H), (15, 15, 18)); x = 0
for t in tiles: c.paste(t, (x, 0)); x += t.width + 6
c.save(out, quality=92)
