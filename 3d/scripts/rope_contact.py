import sys, os
from PIL import Image, ImageDraw
d = sys.argv[1]
row1 = [("main_f001.png", "descent 0 (f1)"), ("main_f120.png", "descent 0.5 (f120)"), ("main_f240.png", "descent 1 (f240)")]
row2 = [("windlass_f001.png", "windlass f1"), ("windlass_f120.png", "windlass f120 (drum turned)"), ("knot_f001.png", "knot / lashing"),
        ("harness_f120.png", "harness f120"), ("under_f240.png", "slings crossing under, f240")]
W = 1350
def row(items, h):
    ims = [Image.open(os.path.join(d, f)).convert("RGB") for f, _ in items]
    ims = [i.resize((int(i.width * h / i.height), h)) for i in ims]
    tw = sum(i.width for i in ims); scale = min(1.0, W / tw)
    ims = [i.resize((int(i.width * scale), int(h * scale))) for i in ims]
    out = Image.new("RGB", (W, int(h * scale)), (40, 40, 40)); x = (W - sum(i.width for i in ims)) // 2
    dr = ImageDraw.Draw(out)
    for im, (_, lab) in zip(ims, items):
        out.paste(im, (x, 0)); dr.rectangle([x, 0, x + 8 * len(lab) + 8, 18], fill=(0, 0, 0)); dr.text((x + 4, 3), lab, fill=(255, 255, 255)); x += im.width
    return out
r1, r2 = row(row1, 800), row(row2, 400)
sheet = Image.new("RGB", (W, r1.height + r2.height + 6), (40, 40, 40))
sheet.paste(r1, (0, 0)); sheet.paste(r2, (0, r1.height + 6))
sheet.save(os.path.join(d, "rope_contact_sheet.png")); print(sheet.size)
