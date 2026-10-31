# FRONT-view site layers for the windlass section (Cycles, hero rev7 / v25 light family).
#   block_rope.png          block + sling + long rope, fully lowered, plumb (no swing)
#   windlass_back_NN.png    windlass parts BEHIND the rope plane (camera clip), crank loop frame NN
#   windlass_front_NN.png   windlass parts IN FRONT of the rope plane
#   layers.json             same fields as site_rope_v5/layers.json (+ view/light info)
# One orthographic camera -> all layers stack pixel-exact; lowering = pure translateY (rope stays plumb on screen).
# usage: blender -b scene_windlass_front.blend -P front_layers.py -- OUT_DIR SPP PCT [JOBS]
#   PCT  = resolution percentage of the 3200x8192 canvas (drafts ~30, finals 100)
#   JOBS = comma list of: block_rope, w00..w11 (both halves of that crank frame), json   (default: everything)
# Resumable: every PNG that already exists (size > 0) is skipped; json is cheap and always rewritten.
# env: EXPO (view exposure), KEY/SKY/RIM/BOUNCE/WORLD (light strengths), ELEV (camera elevation deg)
import bpy, sys, json, math, os, numpy as np
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

argv = sys.argv[sys.argv.index("--") + 1:]
out, spp, pct = argv[0], int(argv[1]), int(argv[2])
jobs = argv[3].split(",") if len(argv) > 3 and argv[3] else None
def want(j): return jobs is None or j in jobs
os.makedirs(out, exist_ok=True)
E = lambda k, d: float(os.environ.get(k, d))
sc = bpy.context.scene; O = bpy.data.objects
W, H = 3200, 8192                                     # shared canvas (as site_rope_v5)
ELEV = E("ELEV", 5.0)                                 # small downward look: drum/sills read as 3D, rope still vertical

# ---------------------------------------------------------------- pose: fully lowered, plumb
ctl = O["Descent_Control"]
if ctl.animation_data: ctl.animation_data_clear()
ctl["descent"] = 1.0
for n in ("Hang_Pivot", "Hang_Drop"):
    o = O[n]
    if o.animation_data and o.animation_data.action:
        for fc in list(o.animation_data.action.fcurves):
            if fc.data_path == "rotation_euler": o.animation_data.action.fcurves.remove(fc)
    o.rotation_euler = (0, 0, 0)
sc.frame_set(1); bpy.context.view_layer.update()

def descendants(root):
    s = {root.name}
    for o in O:
        p = o.parent
        while p:
            if p.name == root.name: s.add(o.name); break
            p = p.parent
    return s
windlass = descendants(O["Windlass"]) | {"Rope_DrumCoil"}
hanging = (descendants(O["Hang_Pivot"]) - {"Hang_Pivot"}) | {"Rope_FreeSpan"}

def verts(names, step=1):
    """true evaluated vertex positions (curve bound_box is unreliable: the GN rope curves report huge boxes)"""
    dg = bpy.context.evaluated_depsgraph_get(); pts = []
    for n in names:
        o = O[n]
        if o.type not in ('MESH', 'CURVE'): continue
        e = o.evaluated_get(dg)
        try:
            me = e.to_mesh()
            a = np.empty(len(me.vertices) * 3); me.vertices.foreach_get("co", a); e.to_mesh_clear()
            a = a.reshape(-1, 3)[::step]
            M = np.array(e.matrix_world); a = a @ M[:3, :3].T + M[:3, 3]
        except Exception:
            a = np.array([e.matrix_world @ Vector(c) for c in e.bound_box])
        if len(a): pts.append(a)
    return np.vstack(pts)

# crank loop: drum driven directly (driver removed); find the lowering direction first
drum = O["Drum"]; base = drum.rotation_euler.copy()
ctl["descent"] = 0.99; sc.frame_set(1); a1 = drum.rotation_euler.x
ctl["descent"] = 1.00; sc.frame_set(1); a2 = drum.rotation_euler.x
sign = 1.0 if a2 >= a1 else -1.0
base = drum.rotation_euler.copy()
drum.driver_remove("rotation_euler")
if drum.animation_data and drum.animation_data.action:
    for fc in list(drum.animation_data.action.fcurves):
        if fc.data_path == "rotation_euler": drum.animation_data.action.fcurves.remove(fc)
NF = 12
def set_crank(i):
    drum.rotation_euler = base; drum.rotation_euler.x = base.x + sign * i * 2 * math.pi / NF
    bpy.context.view_layer.update()
bw = np.vstack([verts(windlass, 1) for i in range(NF) if set_crank(i) is None])   # every crank pose -> one crop
set_crank(0)
bh = verts(hanging, 1)
allp = np.vstack([bw, bh])

# ---------------------------------------------------------------- camera: orthographic FRONT (looks along +Y)
el = math.radians(ELEV)
d = Vector((0.0, -math.cos(el), math.sin(el)))        # target -> camera
right = Vector((1, 0, 0)); up = d.cross(right).normalized()   # screen up = (0, sin, cos)
pivot = Vector(O["Hang_Pivot"].matrix_world.translation)
u = (allp - np.array(pivot)) @ np.array(right)
v = (allp - np.array(pivot)) @ np.array(up)
half_w = max(abs(u.min()), abs(u.max())) * 1.06        # rope (pivot) exactly on the vertical centre line
height = (v.max() - v.min()) * 1.05
scale = max(height, 2 * half_w * H / W)
vc = (v.max() + v.min()) / 2
_g = out + "/geom.json"
if os.path.exists(_g): _c = json.load(open(_g)); scale, vc = _c.get("scale", scale), _c.get("vc", vc)   # frozen per OUT dir
cam = sc.camera; cam.data.type = 'ORTHO'; cam.data.ortho_scale = scale
cam.data.shift_x = cam.data.shift_y = 0.0
cam.location = pivot + up * vc + d * 20.0
cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = W, H, pct
sc.render.pixel_aspect_x = sc.render.pixel_aspect_y = 1
bpy.context.view_layer.update()
ppm = H / scale
def px(p):
    q = world_to_camera_view(sc, cam, Vector(p)); return (q.x * W, (1 - q.y) * H)   # canvas px, top-left origin

# ---------------------------------------------------------------- light: hero rev7 (variant 25) family
# Suns (direction-only) instead of the hero's nearby area lights: the block layer is lit once at the fully lowered
# position and slid up on the site, so the light must not change with height. Sun angle = hero softness (key 1.4 m @ 2.2 m).
from mathutils import Color
for o in O:
    if o.type == 'LIGHT': o.hide_render = True; o.hide_viewport = True
BLUE = (0.0, 0.443, 1.0)            # AgX-compensated #77D9FF (brand_recolor.py)
def sun(name, col, e, az, el_, ang, spec=1.0, shadow=True):
    ld = bpy.data.lights.new(name, 'SUN'); ld.color = col; ld.energy = e; ld.angle = math.radians(ang)
    ld.specular_factor = spec; ld.use_shadow = shadow
    o = bpy.data.objects.new(name, ld); sc.collection.objects.link(o)
    a, b = math.radians(az), math.radians(el_)
    dirv = Vector((math.sin(a) * math.cos(b), -math.cos(a) * math.cos(b), math.sin(b)))   # towards the light
    o.location = pivot + dirv * 6; o.rotation_euler = (-dirv).to_track_quat('-Z', 'Y').to_euler()
    o.visible_camera = False
    return o
# az: 0 = from the camera side, negative = screen-left (-X), +-180 = from behind
sun("KeyChamp", (1.0, 0.73, 0.40), E("KEY", 3.2), -42, 40, 32, spec=0.5)          # upper front-left, large & soft
sun("TopNeutral", (1.0, 0.95, 0.90), E("SKY", 0.45), 10, 78, 60, spec=0.4)        # hero "Skylight"
sun("RimBlue", BLUE, E("RIM", 2.2), 140, 22, 8, spec=0.35)                         # back, opposite (right) side
sun("BounceNeutral", (1.0, 0.95, 0.90), E("BOUNCE", 0.18), 0, -28, 60, spec=0.0, shadow=False)
w = sc.world; w.use_nodes = True
bg = next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND')
for l in list(bg.inputs[0].links): w.node_tree.links.remove(l)
bg.inputs[0].default_value = (1.0, 0.97, 0.93, 1); bg.inputs[1].default_value = E("WORLD", 0.04)
vs = sc.view_settings; vs.view_transform = 'AgX'; vs.look = 'AgX - Medium High Contrast'; vs.exposure = E("EXPO", -0.5)
vs.gamma = 1.0; sc.display_settings.display_device = 'sRGB'

# ---------------------------------------------------------------- material grading (on the scene copy, at runtime)
# client: marble clean ivory (the procedural marble carries rust-orange stains), wood natural (not orange)
def grade(mat_name, sat, val=1.0):
    m = bpy.data.materials[mat_name]; nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'); inp = b.inputs['Base Color']
    if not inp.is_linked or (sat == 1.0 and val == 1.0): return
    src = inp.links[0].from_socket; hs = nt.nodes.new('ShaderNodeHueSaturation')
    hs.inputs['Saturation'].default_value = sat; hs.inputs['Value'].default_value = val
    nt.links.new(src, hs.inputs['Color']); nt.links.new(hs.outputs['Color'], inp)
grade("Marble", E("MARBLE_SAT", 0.45), E("MARBLE_VAL", 1.0))
grade("Wood_Aged", E("WOOD_SAT", 0.75), E("WOOD_VAL", 1.0))
grade("Rope_Hemp", E("ROPE_SAT", 0.8), 1.0)
SSS = os.environ.get("SSS", "burley")         # marble SSS radius is 6 mm: burley ~ same look, far cheaper than random walk
mb = next(n for n in bpy.data.materials["Marble"].node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
if SSS == "off": mb.inputs['Subsurface Weight'].default_value = 0.0
elif SSS == "burley": mb.subsurface_method = 'BURLEY'

# ---------------------------------------------------------------- render settings (Cycles)
sc.render.engine = 'CYCLES'; C = sc.cycles
C.device = 'CPU'; C.samples = spp; C.use_adaptive_sampling = True; C.adaptive_threshold = 0.02; C.adaptive_min_samples = 16
C.use_denoising = True; C.denoiser = 'OPENIMAGEDENOISE'; C.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
C.denoising_prefilter = 'ACCURATE'
C.max_bounces = 8; C.diffuse_bounces = int(E("DIFF", 1)); C.glossy_bounces = 3; C.transmission_bounces = 4; C.transparent_max_bounces = 8
C.sample_clamp_indirect = 8.0; C.caustics_reflective = False; C.caustics_refractive = False
sc.render.threads_mode = 'FIXED'; sc.render.threads = int(os.environ.get("THREADS", "3"))   # CPU shared with other renders
sc.render.film_transparent = True
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'
sc.render.image_settings.color_depth = '8'
sc.render.use_border = True; sc.render.use_crop_to_border = True
sc.render.use_persistent_data = True

def rect(pts, pad=32):
    # vectorised ortho projection of ALL vertices (camera has no shift; canvas centre = camera axis)
    q = pts - np.array(cam.location)
    xy = np.stack([W / 2 + (q @ np.array(right)) * ppm, H / 2 - (q @ np.array(up)) * ppm], 1)
    x0, y0 = max(0, int(xy[:, 0].min()) - pad), max(0, int(xy[:, 1].min()) - pad)
    x1, y1 = min(W, int(xy[:, 0].max()) + pad + 1), min(H, int(xy[:, 1].max()) + pad + 1)
    return {"x": x0, "y": y0, "w": x1 - x0, "h": y1 - y0}
def render(visible, r, path, near=0.01, far=1000.0):
    if os.path.exists(path) and os.path.getsize(path) > 0: print("SKIP", path, flush=True); return
    cam.data.clip_start, cam.data.clip_end = near, far
    for o in O:
        if o.type in ('MESH', 'CURVE'): o.hide_render = o.name not in visible
    sc.render.border_min_x, sc.render.border_max_x = r["x"] / W, (r["x"] + r["w"]) / W
    sc.render.border_min_y, sc.render.border_max_y = 1 - (r["y"] + r["h"]) / H, 1 - r["y"] / H
    sc.render.filepath = path + ".tmp.png"                                   # atomic: no half-written layer on restart
    import time; t = time.time()
    bpy.ops.render.render(write_still=True); os.replace(path + ".tmp.png", path)
    print("TIME %.1fs" % (time.time() - t), path, flush=True)
    cam.data.clip_start, cam.data.clip_end = 0.01, 1000.0
    print("RENDERED", path, flush=True)

layers = {}
rb, rw = rect(bh), rect(bw)
# freeze the crops on the first run of an OUT dir: GN rope vertex order varies run-to-run (+-3 px), and every strip /
# layer of one OUT dir must share exactly the same rects
gp = out + "/geom.json"
if os.path.exists(gp):
    g = json.load(open(gp)); rb, rw = g["rb"], g["rw"]
else:
    json.dump({"rb": rb, "rw": rw, "ppm": ppm, "pct": pct, "scale": scale, "vc": vc}, open(gp, "w"))
print("GEOM", json.dumps({"ppm": round(ppm, 1), "scale": scale, "rb": rb, "rw": rw, "pivot": px(pivot)}), flush=True)
layers["block_rope"] = rb
rope_depth = (pivot - cam.location).dot(-d)        # distance camera -> rope plane (split plane)
for i in range(NF):
    layers["windlass_front_%02d" % i] = rw; layers["windlass_back_%02d" % i] = rw

# ---- FINAL strip mode (env STRIPS=1): every layer is rendered as horizontal strips (+OV px overlap for OIDN context)
# into OUT/strips/, so one blender run never needs > 8 min; a run stops starting new strips after BUDGET s.
# stitch_layers.py assembles finished layers. Strip files are atomic (tmp + rename) -> resumable after any kill.
import time
T0 = time.time(); STRIPS = os.environ.get("STRIPS") == "1"; BUDGET = E("BUDGET", 200)
SH = {"block": int(E("STRIP_H_BLOCK", 96)), "wl": int(E("STRIP_H_WL", 490))}; OV = int(E("OV", 16))
manifest = {}
def strip_plan(r, sh):
    plan = []
    for y in range(r["y"], r["y"] + r["h"], sh):
        c0, c1 = y, min(y + sh, r["y"] + r["h"])
        a0, a1 = max(r["y"], c0 - OV), min(r["y"] + r["h"], c1 + OV)
        plan.append({"core": [c0, c1], "rendered": [a0, a1]})
    return plan
class OutOfBudget(Exception): pass
def render_layer(visible, r, name, kind, **kw):
    path = out + "/" + name + ".png"
    if not STRIPS: return render(visible, r, path, **kw)
    if os.path.exists(path) and os.path.getsize(path) > 0: return
    plan = strip_plan(r, SH[kind]); manifest[name] = {"rect": r, "strips": []}
    os.makedirs(out + "/strips", exist_ok=True)
    for k, st in enumerate(plan):
        sp = "%s/strips/%s__s%02d.png" % (out, name, k); st["file"] = os.path.basename(sp); manifest[name]["strips"].append(st)
        if os.path.exists(sp) and os.path.getsize(sp) > 0: continue
        if time.time() - T0 > BUDGET: raise OutOfBudget()
        a0, a1 = st["rendered"]
        render(visible, {"x": r["x"], "y": a0, "w": r["w"], "h": a1 - a0}, sp, **kw)
try:
    if want("block_rope"):
        render_layer(hanging, rb, "block_rope", "block")
    for i in range(NF):
        if not want("w%02d" % i): continue
        set_crank(i)
        render_layer(windlass, rw, "windlass_front_%02d" % i, "wl", far=rope_depth)
        render_layer(windlass, rw, "windlass_back_%02d" % i, "wl", near=rope_depth)
    print("ALL STRIPS DONE" if STRIPS else "ALL DONE", flush=True)
except OutOfBudget:
    print("BUDGET REACHED - rerun to continue", flush=True)
if STRIPS:          # full plan (all layers) for the stitcher, independent of where this run stopped
    for i in range(NF):
        for nm, kw in (("windlass_front_%02d" % i, None), ("windlass_back_%02d" % i, None)):
            if nm not in manifest:
                manifest[nm] = {"rect": rw, "strips": [dict(st, file="%s__s%02d.png" % (nm, k)) for k, st in enumerate(strip_plan(rw, SH["wl"]))]}
    if "block_rope" not in manifest:
        manifest["block_rope"] = {"rect": rb, "strips": [dict(st, file="block_rope__s%02d.png" % k) for k, st in enumerate(strip_plan(rb, SH["block"]))]}
    json.dump(manifest, open(out + "/strips_manifest.json", "w"), indent=1)
set_crank(0)

# ---------------------------------------------------------------- placement data (same fields as site_rope_v5)
drop_m = 3.0
p0 = px(pivot); p1 = px(pivot - Vector((0, 0, drop_m)))
drop_px = p1[1] - p0[1]                                        # screen drop of 3 m world (x cos(elev))
info = {
    "canvas": {"w": W, "h": H}, "px_per_m": ppm,
    "layers": layers,
    "pivot_px": p0,
    "clip_block_layer_above_y_px": p0[1],
    "drop_total_px": drop_px,
    "block_offset_y_px": "translateY = -(1 - descent) * drop_total_px",
    "windlass_loop": {"frames": NF, "degrees_per_frame": 360 / NF, "drum_turns_full_descent": drop_m / (0.105 * 2 * math.pi)},
    "stack_order": ["windlass_back_NN (bottom)", "block_rope", "windlass_front_NN (top)"],
    "swing": {"amplitude_deg": [1.5, 3.0], "period_s_short_rope": 2.4, "period_s_long_rope": 4.4, "damping_per_s": 0.15},
    "view": {"type": "front orthographic", "elevation_deg": ELEV, "ortho_scale_m": scale,
             "note": "rope x frozen at its fully-lowered drum position (canvas centre); render pct=%d" % pct},
}
if want("json"):
    json.dump(info, open(out + "/layers.json", "w"), indent=2)
print("LAYERS DONE", json.dumps({"ppm": round(ppm, 1), "pivot": p0, "drop_px": drop_px, "rb": rb, "rw": rw}), flush=True)
