# compare.py OUT "labelA" "labelB" A1 B1 [A2 B2 ...]  -> rows of (A | B) pairs
import sys
from PIL import Image, ImageDraw
out, la, lb = sys.argv[1:4]; fs = sys.argv[4:]
pairs = [(fs[i], fs[i + 1]) for i in range(0, len(fs), 2)]
W, H = 600, 800
s = Image.new('RGB', (W * 2, H * len(pairs)), (15, 15, 18)); d = ImageDraw.Draw(s)
for r, (a, b) in enumerate(pairs):
    for c, f in enumerate((a, b)):
        im = Image.open(f).convert('RGB').resize((W, H)); s.paste(im, (c * W, r * H))
    d.text((10, r * H + 10), la, fill=(255, 255, 0)); d.text((W + 10, r * H + 10), lb, fill=(255, 255, 0))
s.save(out)
