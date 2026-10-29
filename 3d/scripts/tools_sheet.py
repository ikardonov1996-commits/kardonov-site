# contact sheet of tools renders on dark bg
from PIL import Image, ImageDraw, ImageFont
import os
O = "/tmp/claude-0/-home-user-kardonov-site/cb30cd45-1b88-5b9b-b3ff-480343f6cfce/scratchpad/out/tools"
names = ["hammer_front", "hammer_side", "hammer_34", "hammer_top", "hammer_head", "hammer_grip", "hammer_site",
         "chisel_front", "chisel_side", "chisel_34", "chisel_end", "chisel_head", "chisel_tip", "chisel_site", "hero"]
C, cols = 380, 5
rows = (len(names) + cols - 1) // cols
sheet = Image.new("RGB", (cols * C, rows * C), (22, 22, 24)); d = ImageDraw.Draw(sheet)
try: font = ImageFont.truetype("DejaVuSans.ttf", 15)
except Exception: font = ImageFont.load_default()
for k, n in enumerate(names):
    p = f"{O}/{n}.png" if n.endswith("_site") else f"{O}/tools_{n}.png"
    if not os.path.exists(p): continue
    im = Image.open(p).convert("RGBA").resize((C, C), Image.LANCZOS)
    bg = Image.new("RGBA", (C, C), (22, 22, 24, 255)); bg.alpha_composite(im)
    x, y = (k % cols) * C, (k // cols) * C
    sheet.paste(bg.convert("RGB"), (x, y)); d.text((x + 8, y + 6), n, fill=(240, 200, 120), font=font)
sheet.save(f"{O}/tools_contact_sheet.png"); print("ok", sheet.size)
