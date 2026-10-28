# Site layers for the "block lowered from a windlass" section (no video):
#   block_rope.png        block + sling + long rope (pose: fully lowered, hanging plumb, no swing)
#   windlass_NN.png       windlass, drum + crank rotated NN*15 deg (24-frame loop = 1 revolution)
#   layers.json           pixel placement of every layer on one shared canvas + pivot / drop / clip data
# All layers come from one orthographic camera, so they line up pixel-exact on the canvas.
# usage: blender -b scene_rope_windlass.blend -P site_layers.py -- OUT_DIR SAMPLES
import bpy, sys, json, math, os, numpy as np
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

argv = sys.argv[sys.argv.index("--") + 1:]
out, samples = argv[0], int(argv[1])
os.makedirs(out, exist_ok=True)
sc = bpy.context.scene; O = bpy.data.objects
W, H = 3200, 8192                                    # shared canvas

# ---- pose: fully lowered, plumb (no baked swing/twist)
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
dg = bpy.context.evaluated_depsgraph_get()
def bbox(names):
    pts = []
    for n in names:
        o = O[n]
        if o.type not in ('MESH', 'CURVE'): continue
        e = o.evaluated_get(dg)
        pts += [e.matrix_world @ Vector(c) for c in e.bound_box]
    return np.array(pts)
bw, bh = bbox(windlass), bbox(hanging)
allp = np.vstack([bw, bh])

# ---- camera: orthographic, horizontal 3/4 view (same direction as the carving stages)
d = Vector((1.35, -3.6, 0.0)).normalized()
right = Vector((-d.y, d.x, 0)).normalized()
ctr = Vector(allp.mean(0))
u = (allp - np.array(ctr)) @ np.array(right); z = allp[:, 2]
height = (z.max() - z.min()) * 1.06; width = (u.max() - u.min()) * 1.10
scale = max(height, width * H / W)                    # ortho_scale spans the longer (vertical) side
cam = sc.camera; cam.data.type = 'ORTHO'; cam.data.ortho_scale = scale
cam.location = Vector((ctr.x, ctr.y, (z.max() + z.min()) / 2)) + d * 20.0
cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = W, H, 100
bpy.context.view_layer.update()
ppm = H / scale                                         # pixels per metre
def px(p):
    v = world_to_camera_view(sc, cam, Vector(p)); return (v.x * W, (1 - v.y) * H)   # top-left origin

# ---- render settings
sc.render.engine = 'BLENDER_EEVEE_NEXT'; sc.eevee.taa_render_samples = samples   # fast: no overlapping shells here
sc.render.film_transparent = True
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'
sc.render.use_border = True; sc.render.use_crop_to_border = True
def render_crop(names_visible, pts, path, pad=24, near=0.01, far=1000.0):
    cam.data.clip_start, cam.data.clip_end = near, far
    for o in O:
        if o.type in ('MESH', 'CURVE'): o.hide_render = o.name not in names_visible
    xy = np.array([px(p) for p in pts])
    x0, y0 = max(0, int(xy[:, 0].min()) - pad), max(0, int(xy[:, 1].min()) - pad)
    x1, y1 = min(W, int(xy[:, 0].max()) + pad), min(H, int(xy[:, 1].max()) + pad)
    sc.render.border_min_x, sc.render.border_max_x = x0 / W, x1 / W
    sc.render.border_min_y, sc.render.border_max_y = 1 - y1 / H, 1 - y0 / H
    sc.render.filepath = path
    if not (os.path.exists(path) and os.path.getsize(path) > 0):   # resumable after container restarts
        bpy.ops.render.render(write_still=True)
    cam.data.clip_start, cam.data.clip_end = 0.01, 1000.0
    return {"x": x0, "y": y0, "w": x1 - x0, "h": y1 - y0}

layers = {}
layers["block_rope"] = render_crop(hanging, bh, out + "/block_rope.png")
print("LAYER block_rope", layers["block_rope"], flush=True)

# ---- windlass loop: drive the drum directly (driver removed), 24 steps = one revolution
drum = O["Drum"]
base = drum.rotation_euler.copy()
ctl["descent"] = 0.99; sc.frame_set(1); a1 = drum.rotation_euler.x
ctl["descent"] = 1.00; sc.frame_set(1); a2 = drum.rotation_euler.x
sign = 1.0 if a2 >= a1 else -1.0                         # turning direction while lowering
drum.driver_remove("rotation_euler")
if drum.animation_data and drum.animation_data.action:
    for fc in list(drum.animation_data.action.fcurves):
        if fc.data_path == "rotation_euler": drum.animation_data.action.fcurves.remove(fc)
wpts = bw.copy()
crank_r = 0.40                                           # crank sweeps a circle: widen the crop for every pose
ax = Vector(O["Axle"].matrix_world.translation)
for ang in np.linspace(0, 2 * np.pi, 16, endpoint=False):
    wpts = np.vstack([wpts, [np.array(ax) + np.array([0.9, 0, 0]) + crank_r * np.array([0, math.sin(ang), math.cos(ang)])]])
rope_depth = (Vector(O["Hang_Pivot"].matrix_world.translation) - cam.location).dot(-d)
NF = 12
for i in range(NF):
    drum.rotation_euler = base; drum.rotation_euler.x = base.x + sign * i * 2 * math.pi / NF
    bpy.context.view_layer.update()
    # depth split at the rope plane: parts nearer the camera go IN FRONT of the block, the rest BEHIND it
    layers["windlass_front_%02d" % i] = render_crop(windlass, wpts, out + "/windlass_front_%02d.png" % i, far=rope_depth)
    layers["windlass_back_%02d" % i] = render_crop(windlass, wpts, out + "/windlass_back_%02d.png" % i, near=rope_depth)
    print("LAYER windlass", i, flush=True)

# ---- placement data for the site
pivot = O["Hang_Pivot"].matrix_world.translation
drop_m = 3.0
info = {
    "canvas": {"w": W, "h": H}, "px_per_m": ppm,
    "layers": layers,
    "pivot_px": px(pivot),                                       # rope leaves the drum here: swing origin
    "clip_block_layer_above_y_px": px(pivot)[1],                 # hide the rope above this line (it is "on the drum")
    "drop_total_px": drop_m * ppm,                               # block_rope is drawn fully lowered:
    "block_offset_y_px": "translateY = -(1 - descent) * drop_total_px",
    "windlass_loop": {"frames": NF, "degrees_per_frame": 360 / NF, "drum_turns_full_descent": drop_m / (0.105 * 2 * math.pi)},
    "stack_order": ["windlass_back_NN (bottom)", "block_rope", "windlass_front_NN (top)"],
    "swing": {"amplitude_deg": [1.5, 3.0], "period_s_short_rope": 2.4, "period_s_long_rope": 4.4, "damping_per_s": 0.15},
}
json.dump(info, open(out + "/layers.json", "w"), indent=2)
print("LAYERS DONE", json.dumps({"ppm": round(ppm, 1), "pivot": info["pivot_px"]}))
