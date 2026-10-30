# v6 post: glow raw (emission pass -> fog glow, RGB on black) -> RGBA glow layer in the exact brand colour
# (rgb = brand hex everywhere, alpha = glow intensity), on-dark previews (site + glow screen-blended on #0f0f12),
# profiles.json (keypoints for the strike animation) and profiles_preview.jpg.
# usage: python3 tools_glow_post.py [src_dir]   (src_dir holds r_*.png, glowraw_*.png, r_*_profile.json)
import json, math, os, shutil, sys
import numpy as np
from PIL import Image, ImageDraw
# tlight copy: renders AND outputs live in the given dir (never touches out/tools); + key-point check vs out/tools/profiles.json
O = sys.argv[1]; SRC = O
REF = "/tmp/claude-0/-home-user-kardonov-site/cb30cd45-1b88-5b9b-b3ff-480343f6cfce/scratchpad/out/tools/profiles.json"
BG = (15, 15, 18)
BRAND = {"hammer": "FCCB84", "chisel": "77D9FF"}          # human champagne / AI blue
hexrgb = lambda h: np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255

def glow_layer(raw, tool):
    g = np.asarray(Image.open(raw).convert("RGB")).astype(np.float32) / 255
    a = g.max(axis=2, keepdims=True)
    col = np.broadcast_to(hexrgb(BRAND[tool]), g.shape)
    return Image.fromarray((np.concatenate([col, a], 2) * 255 + 0.5).astype(np.uint8), "RGBA")

def on_dark(beauty, glow, size=None):
    bg = Image.new("RGBA", beauty.size, (*BG, 255)); bg.alpha_composite(beauty)
    return screen(bg, glow)

def screen(base_rgba, glow):                   # what the site does with mix-blend-mode: screen
    base = np.asarray(base_rgba.convert("RGB")).astype(np.float32) / 255
    gl = np.asarray(glow).astype(np.float32) / 255
    gp = gl[..., :3] * gl[..., 3:4]
    return Image.fromarray(((1 - (1 - base) * (1 - gp)) * 255 + 0.5).astype(np.uint8))

# ---- 3/4 site images + profiles: copy beauty, build glow, previews
for tool in ("hammer", "chisel"):
    for view, name, glowname in (("site", f"{tool}_site", f"{tool}_glow"), ("profile", f"{tool}_profile", f"{tool}_profile_glow")):
        b, r = f"{SRC}/r_{tool}_{view}.png", f"{SRC}/glowraw_{tool}_{view}.png"
        if not (os.path.exists(b) and os.path.exists(r)): print("MISSING", tool, view); continue
        shutil.copy(b, f"{O}/{name}.png")
        if os.path.abspath(r) != os.path.abspath(f"{O}/glowraw_{name}.png"): shutil.copy(r, f"{O}/glowraw_{name}.png")
        gl = glow_layer(r, tool); gl.save(f"{O}/{glowname}.png")
        beauty = Image.open(b).convert("RGBA")
        assert beauty.size == gl.size, (beauty.size, gl.size)
        on_dark(beauty, gl).save(f"{O}/{name}_with_glow_on_dark.jpg", quality=92)
        if view == "site":
            bg = Image.new("RGBA", beauty.size, (*BG, 255)); bg.alpha_composite(beauty)
            bg.convert("RGB").save(f"{O}/{name}_on_dark.jpg", quality=92)
        print(tool, view, beauty.size, "glow max alpha", gl.getextrema()[3])

# ---- profiles.json
P = {}
for tool in ("hammer", "chisel"):
    jp = f"{SRC}/r_{tool}_profile.json"
    if not os.path.exists(jp): continue
    j = json.load(open(jp))
    P[tool] = {"image": f"{tool}_profile.png", "glow": f"{tool}_profile_glow.png", "width": j["width"], "height": j["height"],
               "px_per_m": round(j["px_per_m"], 2), "points": j["points_px"]}
if len(P) == 2:
    P["hammer"]["vectors"] = {"handle_up": [0, -1], "striking_face_normal": [-1, 0]}
    P["hammer"]["notes"] = ("Double-faced head: striking_face_center = left face (image -x), striking_face_center_alt = "
                            "right face. handle_pivot_grip_end = bottom end of the pommel on the handle axis; grip_center = middle of the leather grip.")
    P["chisel"]["vectors"] = {"axis_up": [0, -1]}
    P["chisel"]["notes"] = "blade edge is seen end-on (wedge taper in profile); blade_tip = cutting edge centre, striking_top_center = centre of the butt top."
    hf, hp = P["hammer"]["points"]["striking_face_center"], P["hammer"]["points"]["handle_pivot_grip_end"]
    P["strike_pose_example"] = {
        "description": "as in profiles_preview.jpg: scale chisel by hammer.px_per_m/chisel.px_per_m (true relative size), "
                       "rotate the hammer 90deg counter-clockwise (screen) so its left face points down, put hammer striking_face_center on chisel striking_top_center",
        "hammer_rotation_deg_ccw_at_impact": 90,
        "face_to_pivot_distance_px": round(math.dist(hf, hp), 1)}
    P["coordinates"] = "pixels in each PNG, origin top-left, x right, y down; glow PNGs share the canvas of their beauty PNG"
    P["brand_colours"] = {"hammer_glow": "#FCCB84", "chisel_glow": "#77D9FF"}
    json.dump(P, open(f"{O}/profiles.json", "w"), indent=1); print("profiles.json written")
    ref = json.load(open(REF)); worst = 0.0
    for t in ("hammer", "chisel"):
        k = P[t]["height"] / ref[t]["height"]
        assert abs(P[t]["width"] - ref[t]["width"] * k) <= 2, (t, P[t]["width"], ref[t]["width"])
        assert abs(P[t]["px_per_m"] - ref[t]["px_per_m"] * k) < 0.01 * P[t]["px_per_m"]
        for n, pt in ref[t]["points"].items():
            dd = math.dist([c * k for c in pt], P[t]["points"][n]); worst = max(worst, dd / k)
    print(f"KEYPOINT CHECK vs out/tools/profiles.json: max deviation {worst:.2f} px (at 1600 scale)")

    # ---- preview: (A) upright, side by side, true scale, keypoints marked  (B) strike pose
    def load(tool):
        b = Image.open(f"{O}/{tool}_profile.png").convert("RGBA"); g = Image.open(f"{O}/{tool}_profile_glow.png").convert("RGBA")
        return b, g
    hb, hg = load("hammer"); cb, cg = load("chisel")
    k = P["hammer"]["px_per_m"] / P["chisel"]["px_per_m"]                    # chisel -> hammer scale
    W, H = 2940, 1700
    def place(img, src_pt, dst_pt, s=1.0, deg=0.0):
        t = math.radians(deg); c, si = math.cos(t), math.sin(t)
        # dest = Q + s*R(src-P), R = [[c, si], [-si, c]] (CCW on screen); inverse for PIL
        a, b_, d, e = c / s, -si / s, si / s, c / s
        Qx, Qy = dst_pt; Px, Py = src_pt
        return img.transform((W, H), Image.AFFINE, (a, b_, Px - a * Qx - b_ * Qy, d, e, Py - d * Qx - e * Qy), resample=Image.BICUBIC)
    canvas = Image.new("RGBA", (W, H), (*BG, 255)); glows = []
    # A: hammer upright, chisel upright to its left, both standing on the same baseline
    base_y = 1620
    hpv = P["hammer"]["points"]["handle_pivot_grip_end"]; ctip = P["chisel"]["points"]["blade_tip"]
    A_h = (900, base_y); A_c = (330, base_y)
    for img, gl, sp, dp, s in ((hb, hg, hpv, A_h, 1.0), (cb, cg, ctip, A_c, k)):
        canvas.alpha_composite(place(img, sp, dp, s)); glows.append(place(gl, sp, dp, s))
    # B: strike pose. chisel upright, hammer rotated 90 CCW about its striking face, face on chisel butt
    B_tip = (1520, base_y)
    cbutt = P["chisel"]["points"]["striking_top_center"]
    butt_dst = (B_tip[0] + (cbutt[0] - ctip[0]) * k, B_tip[1] + (cbutt[1] - ctip[1]) * k)
    canvas.alpha_composite(place(cb, ctip, B_tip, k)); glows.append(place(cg, ctip, B_tip, k))
    canvas.alpha_composite(place(hb, hf, butt_dst, 1.0, 90)); glows.append(place(hg, hf, butt_dst, 1.0, 90))
    out = canvas
    for g in glows: out = screen(out, g).convert("RGBA")
    d = ImageDraw.Draw(out)
    def mark(p, col):
        x, y = p; d.ellipse((x - 9, y - 9, x + 9, y + 9), outline=col, width=3); d.line((x - 16, y, x + 16, y), fill=col, width=2); d.line((x, y - 16, x, y + 16), fill=col, width=2)
    for name, p in P["hammer"]["points"].items():
        if name in ("striking_face_center", "handle_pivot_grip_end"):
            mark((A_h[0] + p[0] - hpv[0], A_h[1] + p[1] - hpv[1]), (255, 80, 80))
    for name, p in P["chisel"]["points"].items():
        mark((A_c[0] + (p[0] - ctip[0]) * k, A_c[1] + (p[1] - ctip[1]) * k), (255, 80, 80))
    mark(butt_dst, (255, 80, 80))
    d.line((1300, 60, 1300, H - 60), fill=(45, 45, 52), width=2)
    out.convert("RGB").resize((W // 2, H // 2), Image.LANCZOS).save(f"{O}/profiles_preview.jpg", quality=92)
    print("profiles_preview.jpg written")
