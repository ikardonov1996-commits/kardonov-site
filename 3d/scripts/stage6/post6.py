# glow layers (exact brand RGB, alpha = intensity) + strip of 6 stills on #0f0f12
import numpy as np, subprocess, sys
from PIL import Image
S = "/tmp/claude-0/-home-user-kardonov-site/cb30cd45-1b88-5b9b-b3ff-480343f6cfce/scratchpad"; F = S + "/out/stages_light/final"
for kind, hexc in (("blue", "77D9FF"), ("champ", "FCCB84")):
    g = np.asarray(Image.open(f"{F}/stage_6_glowraw_{kind}.png")).astype(np.float64); g = g / (65535 if g.max() > 255 else 255)
    a = np.clip(g.max(2) if g.ndim == 3 else g, 0, 1); col = np.array([int(hexc[i:i+2], 16) for i in (0, 2, 4)], np.uint8)
    rgba = np.zeros(a.shape + (4,), np.uint8); rgba[..., :3] = col; rgba[..., 3] = (a * 255 + .5).astype(np.uint8)
    Image.fromarray(rgba, "RGBA").save(f"{F}/stage_6_glow_{kind}.png"); print(kind, "alpha max %.3f, px>0.02: %d" % (a.max(), (a > .02).sum()))
names = ["stage_1_Marble_Block", "stage_2_C4_Freed", "stage_3_C5_Point", "stage_4_C6_Claw", "stage_5_Sculpture_HiRes", "stage_6_Cyber_David"]
BG = (15, 15, 18); W, H = 540, 720; c = Image.new("RGB", (W * 6, H), BG)
bl = np.asarray(Image.open(f"{F}/stage_6_glow_blue.png")).astype(float) / 255; ch = np.asarray(Image.open(f"{F}/stage_6_glow_champ.png")).astype(float) / 255
for j, n in enumerate(names):
    im = Image.open(f"{F}/{n}.png").convert("RGBA"); t = Image.new("RGBA", im.size, BG + (255,)); t.alpha_composite(im)
    base = np.asarray(t.convert("RGB")).astype(float) / 255
    if j == 5:   # screen the glow layers on top (as the site would)
        base = 1 - (1 - base) * (1 - bl[..., :3] * bl[..., 3:]) * (1 - ch[..., :3] * ch[..., 3:])
    c.paste(Image.fromarray((base * 255 + .5).astype(np.uint8)).resize((W, H), Image.LANCZOS), (j * W, 0))
c.save(f"{F}/strip6.jpg", quality=92); print("strip6", f"{F}/strip6.jpg")
