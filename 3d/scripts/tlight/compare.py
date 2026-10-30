# old (out/tools, v6 studio light, EEVEE) vs new (tlight, Cycles hero look) -- all with glow, on #0f0f12
# usage: compare.py NEWDIR OUT.jpg [title]
import sys; from PIL import Image, ImageDraw, ImageFont
S = "/tmp/claude-0/-home-user-kardonov-site/cb30cd45-1b88-5b9b-b3ff-480343f6cfce/scratchpad"
OLD = f"{S}/out/tools"; NEW = sys.argv[1]; OUT = sys.argv[2]; title = sys.argv[3] if len(sys.argv) > 3 else ""
BG = (15, 15, 18); H = 620; pad = 16; top = 70
try: F = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22); FB = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 26)
except Exception: F = FB = ImageFont.load_default()
def tile(path, crop_sq=False):
    im = Image.open(path).convert("RGB")
    if crop_sq:   # site views: the tool sits in a square frame -> crop the central 62% width for the sheet
        w, h = im.size; cw = int(w * 0.62); im = im.crop(((w - cw) // 2, 0, (w + cw) // 2, h))
    return im.resize((int(im.width * H / im.height), H), Image.LANCZOS)
rows = []
for tool in ("hammer", "chisel"):
    cells = [("OLD 3/4", tile(f"{OLD}/{tool}_site_with_glow_on_dark.jpg", True)), ("NEW 3/4", tile(f"{NEW}/{tool}_site_with_glow_on_dark.jpg", True)),
             ("OLD profile", tile(f"{OLD}/{tool}_profile_with_glow_on_dark.jpg")), ("NEW profile", tile(f"{NEW}/{tool}_profile_with_glow_on_dark.jpg"))]
    rows.append((tool, cells))
W = max(sum(max(c[1].width, 300) for c in cells) + pad * (len(cells) + 1) for _, cells in rows)
sheet = Image.new("RGB", (W, top + len(rows) * (H + 50 + pad)), BG); d = ImageDraw.Draw(sheet)
d.text((pad, 18), title or "KARDONOV tools - old studio light vs new hero light (DRAFT)", fill=(230, 220, 200), font=FB)
y = top
for tool, cells in rows:
    x = pad
    for lab, im in cells:
        d.text((x, y), f"{tool} - {lab}", fill=(252, 203, 132) if "NEW" in lab else (150, 150, 160), font=F)
        cw = max(im.width, 300); sheet.paste(im, (x + (cw - im.width) // 2, y + 34)); x += cw + pad
    y += H + 50 + pad
sheet.save(OUT, quality=90); print("saved", OUT, sheet.size)
