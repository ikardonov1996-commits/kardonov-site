import sys, os
from PIL import Image, ImageDraw
pre, out = sys.argv[1], sys.argv[2]
order = ["01_front","02_main34","03_armside","04_armfront","05_shoulder_front","06_shoulder_back","07_hand_front","08_hand_back","12_elbow_inner","09_band_front","10_band_back","11_band_34","13_band_left","14_band_right"]
W, H, cols = 360, 480, 6
s = Image.new('RGB', (W * cols, H * 3), (15, 15, 18)); d = ImageDraw.Draw(s)
for i, n in enumerate(order):
    im = Image.open(f"{pre}_{n}.png").convert('RGB').resize((W, H)); x, y = (i % cols) * W, (i // cols) * H
    s.paste(im, (x, y)); d.text((x + 6, y + 6), n, fill=(255, 255, 0))
s.save(out)
