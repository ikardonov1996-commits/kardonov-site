import bpy, sys, os, time
S = "/tmp/claude-0/-home-user-kardonov-site/cb30cd45-1b88-5b9b-b3ff-480343f6cfce/scratchpad"
sys.path.insert(0, S + "/scripts/hero"); import hero_light as H
E = os.environ; OUT = E["OUTDIR"]; os.makedirs(OUT + "/strips", exist_ok=True)
shot, rot, var, scale = E["SHOT"], int(E.get("ROT", "0")), int(E.get("VAR", "42")), float(E.get("SCALE", "1"))
sc = bpy.context.scene; D = bpy.data
H.LAY = OUT; sc.node_tree.nodes["HeroGlowOut"].base_path = OUT
H.build_variants(); H.build_cams(); H.store_base(); H.clean_marble(0.45)
H.set_variant(var); H.set_shot(shot, scale); H.set_rot(rot)
sh = H.SHOTS[shot]; cam = sc.camera
w, h = sh["res"]; vf = 2 * sh["d"] * 18 / sh["lens"]; side_h = vf if sh["fit"] == 'VERTICAL' else vf * h / w
cam.data.shift_y = (sh["frame_z"] - sh["cam_z"]) / (side_h * max(w, h) / h)
W, Hh = sc.render.resolution_x, sc.render.resolution_y
nt = sc.node_tree
# ---- ROWS mode (continuation of the final): one adaptive-height strip per Blender run.
# env: START=nominal first row of this shot's row plan (rows above it are covered by older strips), TARGET s per strip,
#      OV overlap rows, SPP, ADAPT. Pieces: {OUT}/strips/{shot}_r{y0}-{y1}.png (nominal rows [y0,y1), rendered y0-OV..y1+OV)
import json, glob, re
ov = int(E.get("OV", "6")); start = int(E.get("START", "0")); target = min(float(E.get("TARGET", "300")), 270.0)
sc.cycles.samples = int(E.get("SPP", "192")); sc.cycles.adaptive_threshold = float(E.get("ADAPT", "0.015"))
if shot == "A": sc.cycles.samples, sc.cycles.adaptive_threshold = 128, 0.01   # = approved prefinal sampling (A_preview)
nt.nodes["HeroGlowOut"].mute = True
done = [tuple(int(v) for v in re.findall(r"_r(\d+)-(\d+)\.png$", f)[0]) for f in glob.glob(f"{OUT}/strips/{shot}_r*-*.png")]
y = start
for a, b in sorted(done):
    if a == y: y = b
if y >= Hh: print("ROWS_ALL_DONE", shot, flush=True); sys.exit(0)
stf = f"{OUT}/strips/{shot}_rows_state.json"
st = json.load(open(stf)) if os.path.exists(stf) else {"spr": float(E.get("SPR0", "7"))}
if st.get("pending") == y: st["spr"] *= 1.6; print("PREV_TIMEOUT_AT", y, flush=True)   # last attempt here was killed
k = int(max(12, min(400, target / st["spr"]))); y1n = min(Hh, y + k)
if Hh - y1n < 12: y1n = Hh
st["pending"] = y; json.dump(st, open(stf, "w"))
r0, r1 = max(0, y - ov), min(Hh, y1n + ov)
sc.render.use_border = True; sc.render.use_crop_to_border = False
sc.render.border_min_x, sc.render.border_max_x = 0.0, 1.0
sc.render.border_min_y, sc.render.border_max_y = 1 - r1 / Hh, 1 - r0 / Hh
out = f"{OUT}/strips/{shot}_r{y}-{y1n}.png"
sc.render.filepath = out + ".tmp.png"; t0 = time.time(); bpy.ops.render.render(write_still=True); dt = time.time() - t0
os.replace(out + ".tmp.png", out)
spr = dt / (r1 - r0); st = {"spr": max(0.5, spr), "last": [y, y1n, round(dt)]}; json.dump(st, open(stf, "w"))
print("ROWS_DONE", shot, W, Hh, f"nominal {y}-{y1n} rendered {r0}-{r1}", f"{dt:.0f}s", f"{spr:.2f}s/row", time.strftime("%T"), flush=True)
