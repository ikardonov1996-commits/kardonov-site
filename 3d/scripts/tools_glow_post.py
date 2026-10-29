# glow RGB-on-black -> RGBA (alpha = intensity, colour = unpremultiplied glow colour); preview site+glow (screen) on #0f0f12
import numpy as np
from PIL import Image
O = "/tmp/claude-0/-home-user-kardonov-site/cb30cd45-1b88-5b9b-b3ff-480343f6cfce/scratchpad/out/tools"
for t in ("hammer", "chisel"):
    g = np.asarray(Image.open(f"{O}/glowraw_{t}_site.png").convert("RGB")).astype(np.float32) / 255
    a = g.max(axis=2, keepdims=True)
    col = np.where(a > 1e-4, g / np.maximum(a, 1e-4), 0)
    Image.fromarray((np.concatenate([col, a], 2) * 255 + 0.5).astype(np.uint8), "RGBA").save(f"{O}/{t}_glow.png")
    site = Image.open(f"{O}/{t}_site.png").convert("RGBA")
    bg = Image.new("RGBA", site.size, (15, 15, 18, 255)); bg.alpha_composite(site)
    base = np.asarray(bg.convert("RGB")).astype(np.float32) / 255
    glow = col * a                                   # what CSS screen-blends (premultiplied colour)
    out = 1 - (1 - base) * (1 - glow)
    Image.fromarray((out * 255 + 0.5).astype(np.uint8)).save(f"{O}/{t}_site_with_glow_on_dark.jpg", quality=92)
    print(t, "max alpha", float(a.max()))
