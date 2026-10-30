# KARDONOV tools relight (hero rev7 / variant 25 look) -- CYCLES. Run on assets/asset_tools_light.blend (copy); the
# file is NOT saved. Cameras/placement/key points are byte-identical to scripts/tools_render.py (site 3/4 + profiles).
# args after --: out_prefix  view1,view2  [res=800] [samples=96] [force=0]
#   res = site square size AND profile long side (finals: 1600). Profiles must be rendered in a separate run.
# env: GLOW=1 -> emission-only glow raw layer (same recipe as v6: Emit pass -> fog glow, AgX, exposure 0)
#      DRY=1 -> no render (profile json is still written)    LIGHT_* overrides, see P below
import bpy, sys, math, os, json
from mathutils import Vector as V

argv = sys.argv[sys.argv.index("--") + 1:]
PRE = argv[0]; want = argv[1]
RES = int(argv[2]) if len(argv) > 2 else 800
SAMP = int(argv[3]) if len(argv) > 3 else 96
FORCE = len(argv) > 4 and argv[4] == "1"
GLOW = bool(os.environ.get("GLOW"))
D = bpy.data; sc = bpy.context.scene

# ------------------------------------------------------------------ light parameters (draft v2 = L7, after self-review)
P = dict(
    exposure=-0.8, look="AgX - Medium High Contrast",
    # spec: EEVEE-style factor, in Cycles only used as on/off for glossy visibility (top fill + bounce = no reflections)
    # camera-relative placement: az deg from the camera direction, + = image LEFT; el deg; d m (tools ~0.35 m)
    key=dict(col=(1.0, 0.73, 0.40), e=19.0, size=0.75, az=48, el=40, d=1.05, spec=0.25),        # champagne, large soft
    sky=dict(col=(1.0, 0.95, 0.90), e=10.0, size=0.9, az=10, el=78, d=1.1, spec=0.08),          # neutral top fill
    fill=dict(col=(1.0, 0.97, 0.93), e=3.2, size=1.4, az=-55, el=8, d=1.3, spec=0.25),          # neutral fill, shadow side
    rimB=dict(col=(0.0, 0.443, 1.0), e=70.0, size=0.2, size_y=0.7, az=-142, el=24, d=0.95, spec=1.0),  # cool blue rim
    rimC=dict(col=(1.0, 0.72, 0.42), e=5.0, size=0.18, size_y=0.55, az=140, el=22, d=0.95, spec=0.4),   # weak champagne kicker
    bounce=dict(col=(1.0, 0.95, 0.90), e=0.6, size=1.4, az=0, el=-30, d=1.2, spec=0.0),
    # world seen ONLY by glossy rays (metal gets a soft neutral studio to reflect; diffuse lighting = lights only)
    env=dict(bottom=0.015, horizon=0.18, top=0.24, strength=1.0,
             box=1.8, box_cos=0.80, box_col=(1.0, 0.96, 0.91),      # broad neutral-warm softbox around the key direction
             fillb=1.4, fillb_cos=0.75, fillb_col=(0.93, 0.96, 1.0),  # broad cool-neutral card on the fill side (titanium)
             cool=1.0, cool_cos=0.88),                              # blue patch around the rim direction
    # emitters: (camera, diffuse/other, glossy) strength. Camera value sets the look of the tube; diffuse/glossy = spill
    neon=dict(cam=4.0, diff=250.0, gloss=150.0), ring=dict(cam=2.4, diff=250.0, gloss=150.0), amber=dict(cam=3.0, diff=6.0, gloss=2.0),
    # runtime material compensation (asset file untouched): leather back to cream under the champagne key
    mat=dict(leather=(0.70, 0.60, 0.46)),
)
# per-tool overrides: the chisel (AI, cool titanium) gets the champagne key at half saturation -> titanium reads light
# neutral grey instead of bronze; everything else identical.
TOOL = {"C": dict(key=dict(col=(1.0, 0.865, 0.70), e=16.0))}
for k, v in os.environ.items():                     # LIGHT_key_e=20 etc.
    if k.startswith("LIGHT_"):
        a, _, b = k[6:].partition("_")
        if b: P[a][b] = float(v)
        else: P[a] = float(v)

# ------------------------------------------------------------------ render settings
sc.render.engine = 'CYCLES'; cy = sc.cycles
cy.device = 'CPU'; cy.samples = SAMP; cy.use_adaptive_sampling = True; cy.adaptive_threshold = 0.015
cy.use_denoising = True; cy.denoiser = 'OPENIMAGEDENOISE'
try: cy.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
except Exception: pass
cy.max_bounces = 8; cy.diffuse_bounces = 2; cy.glossy_bounces = 3; cy.transmission_bounces = 4; cy.transparent_max_bounces = 4
cy.caustics_reflective = False; cy.caustics_refractive = False; cy.sample_clamp_indirect = 6.0; cy.blur_glossy = 1.0
sc.render.resolution_x = sc.render.resolution_y = RES; sc.render.resolution_percentage = 100
sc.render.film_transparent = True
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'
sc.render.image_settings.color_depth = '8'
vs = sc.view_settings; vs.view_transform = 'AgX'
if GLOW:  vs.look = 'None'; vs.exposure = 0.0          # identical to the v6 glow recipe
else:     vs.look = P["look"]; vs.exposure = P["exposure"]
sc.use_nodes = True; nt = sc.node_tree
for n in list(nt.nodes): nt.nodes.remove(n)
rl = nt.nodes.new('CompositorNodeRLayers'); comp = nt.nodes.new('CompositorNodeComposite')
if GLOW:   # emission pass only -> fog glow (no surfaces, no reflections of the neon)
    bpy.context.view_layer.use_pass_emit = True
    g = nt.nodes.new('CompositorNodeGlare'); g.glare_type = 'FOG_GLOW'; g.quality = 'HIGH'
    g.threshold = 0.3; g.size = int(os.environ.get("GLOW_SIZE", "8")); g.mix = 0.2
    nt.links.new(rl.outputs['Emit'], g.inputs['Image']); nt.links.new(g.outputs['Image'], comp.inputs['Image'])
    sc.render.image_settings.color_mode = 'RGB'
    cy.max_bounces = 0; cy.samples = min(SAMP, 32); cy.use_denoising = False   # emission pass needs no light transport
else:      # beauty: crisp, no compositor glare (the soft halo is the separate glow layer on the site)
    nt.links.new(rl.outputs['Image'], comp.inputs['Image']); nt.links.new(rl.outputs['Alpha'], comp.inputs['Alpha'])

# ------------------------------------------------------------------ world: glossy-only neutral studio gradient
w = sc.world; w.use_nodes = True; wn = w.node_tree
for n in list(wn.nodes): wn.nodes.remove(n)
out = wn.nodes.new('ShaderNodeOutputWorld')
lp = wn.nodes.new('ShaderNodeLightPath'); mix = wn.nodes.new('ShaderNodeMixShader')
b0 = wn.nodes.new('ShaderNodeBackground'); b0.inputs['Color'].default_value = (0, 0, 0, 1); b0.inputs['Strength'].default_value = 0
b1 = wn.nodes.new('ShaderNodeBackground'); b1.inputs['Strength'].default_value = P["env"]["strength"]
tc = wn.nodes.new('ShaderNodeTexCoord'); sep = wn.nodes.new('ShaderNodeSeparateXYZ'); ramp = wn.nodes.new('ShaderNodeValToRGB')
mr = wn.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = -1; mr.inputs['From Max'].default_value = 1
wn.links.new(tc.outputs['Generated'], sep.inputs['Vector'])           # world Generated = view direction
wn.links.new(sep.outputs['Z'], mr.inputs['Value']); wn.links.new(mr.outputs['Result'], ramp.inputs['Fac'])   # z -1..1 -> 0..1
e = ramp.color_ramp.elements; E = P["env"]
e[0].position = 0.0; e[0].color = (E["bottom"],) * 3 + (1,)
e[1].position = 1.0; e[1].color = (E["top"],) * 3 + (1,)
m = e.new(0.5); m.color = (E["horizon"],) * 3 + (1,)
def blob(dirname, kcos, col, k):     # col * k * smoothstep(kcos..1, dot(view, dir))
    dv = wn.nodes.new('ShaderNodeCombineXYZ'); dv.name = dirname
    dt = wn.nodes.new('ShaderNodeVectorMath'); dt.operation = 'DOT_PRODUCT'
    wn.links.new(tc.outputs['Generated'], dt.inputs[0]); wn.links.new(dv.outputs[0], dt.inputs[1])
    mr = wn.nodes.new('ShaderNodeMapRange'); mr.interpolation_type = 'SMOOTHSTEP'
    mr.inputs['From Min'].default_value = kcos; mr.inputs['From Max'].default_value = 1.0
    wn.links.new(dt.outputs['Value'], mr.inputs['Value'])
    sm = wn.nodes.new('ShaderNodeVectorMath'); sm.operation = 'SCALE'; sm.inputs[0].default_value = tuple(x * k for x in col)
    wn.links.new(mr.outputs['Result'], sm.inputs['Scale']); return sm
acc = ramp.outputs['Color']
for nm, kc, col, k in (("ENV_KEY", E["box_cos"], E["box_col"], E["box"]), ("ENV_FILL", E["fillb_cos"], E["fillb_col"], E["fillb"]),
                       ("ENV_COOL", E["cool_cos"], (0.0, 0.443, 1.0), E["cool"])):
    sm = blob(nm, kc, col, k); ad = wn.nodes.new('ShaderNodeVectorMath'); ad.operation = 'ADD'
    wn.links.new(acc, ad.inputs[0]); wn.links.new(sm.outputs['Vector'], ad.inputs[1]); acc = ad.outputs['Vector']
wn.links.new(acc, b1.inputs['Color'])
wn.links.new(lp.outputs['Is Glossy Ray'], mix.inputs['Fac'])
wn.links.new(b0.outputs['Background'], mix.inputs[1]); wn.links.new(b1.outputs['Background'], mix.inputs[2])
wn.links.new(mix.outputs['Shader'], out.inputs['Surface'])

# ------------------------------------------------------------------ emitters: camera vs spill strength (light path)
def split_emission(mname, cfg):
    mt = D.materials[mname]; t = mt.node_tree
    bs = next(n for n in t.nodes if n.type == 'BSDF_PRINCIPLED')
    s = bs.inputs['Emission Strength']
    for l in list(s.links): t.links.remove(l)
    lp = t.nodes.new('ShaderNodeLightPath')
    m1 = t.nodes.new('ShaderNodeMix'); m1.data_type = 'FLOAT'      # glossy ? gloss : diff
    m1.inputs[2].default_value = cfg["diff"]; m1.inputs[3].default_value = cfg["gloss"]
    t.links.new(lp.outputs['Is Glossy Ray'], m1.inputs[0])
    m2 = t.nodes.new('ShaderNodeMix'); m2.data_type = 'FLOAT'      # camera ? cam : m1
    m2.inputs[3].default_value = cfg["cam"]
    t.links.new(m1.outputs[0], m2.inputs[2]); t.links.new(lp.outputs['Is Camera Ray'], m2.inputs[0])
    t.links.new(m2.outputs[0], s)
    try: mt.cycles.emission_sampling = 'FRONT_BACK'
    except Exception: pass
if P["mat"].get("leather"):
    bl = next(n for n in D.materials["Tool_Leather"].node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    if not bl.inputs['Base Color'].is_linked: bl.inputs['Base Color'].default_value = tuple(P["mat"]["leather"]) + (1,)
if GLOW:   # glow raw = v6 strengths (camera rays only matter for the Emit pass)
    split_emission("Tool_GlowBlue", dict(cam=5.0, diff=0.0, gloss=0.0)); split_emission("Tool_GlowBlueRing", dict(cam=2.2, diff=0.0, gloss=0.0))
    split_emission("Tool_GlowAmber", dict(cam=5.0, diff=0.0, gloss=0.0))
else:
    split_emission("Tool_GlowBlue", P["neon"]); split_emission("Tool_GlowBlueRing", P["ring"]); split_emission("Tool_GlowAmber", P["amber"])

# ------------------------------------------------------------------ light rig, rebuilt per shot relative to the camera
for o in [o for o in sc.objects if o.type == 'LIGHT']: D.objects.remove(o, do_unlink=True)
RIG = {}
def build_rig(cam_dir, target, tool="H"):
    PT = {k: (dict(v, **TOOL.get(tool, {}).get(k, {})) if isinstance(v, dict) else v) for k, v in P.items()}
    h = V((cam_dir.x, cam_dir.y, 0)).normalized(); left = V((h.y, -h.x, 0))
    for name, c in PT.items():
        if not isinstance(c, dict) or "e" not in c or name == "env": continue
        o = RIG.get(name)
        if o is None:
            ld = D.lights.new("TL_" + name, 'AREA'); o = D.objects.new("TL_" + name, ld); sc.collection.objects.link(o)
            o.visible_camera = False; RIG[name] = o
        ld = o.data; ld.color = c["col"]; ld.energy = c["e"]; ld.specular_factor = c["spec"]
        if "size_y" in c: ld.shape = 'RECTANGLE'; ld.size = c["size"]; ld.size_y = c["size_y"]
        else: ld.shape = 'DISK'; ld.size = c["size"]
        a, el = math.radians(c["az"]), math.radians(c["el"])
        hd = h * math.cos(a) + left * math.sin(a)
        dirv = (hd * math.cos(el) + V((0, 0, math.sin(el)))).normalized()
        o.location = target + dirv * c["d"]
        o.rotation_euler = (target - o.location).to_track_quat('-Z', 'Y').to_euler()
        o.data.cycles.is_caustics_light = False
        o.visible_glossy = c["spec"] > 0.1      # Cycles ignores specular_factor: spec < 0.1 = light not seen in reflections
        envn = {"key": "ENV_KEY", "fill": "ENV_FILL", "rimB": "ENV_COOL"}.get(name)
        if envn:
            cn = wn.nodes[envn]
            for i in range(3): cn.inputs[i].default_value = dirv[i]
    o = RIG.get("bounce")
    if o: o.data.cycles.cast_shadow = False
    bpy.context.view_layer.update()

# ------------------------------------------------------------------ cameras: copied from tools_render.py (do not edit)
HAM, CHI, CAM = D.objects["Hammer"], D.objects["Chisel"], sc.camera
CENTER = V((0, 0, 0.16))
def kids(e): return [o for o in e.children_recursive if o.type == 'MESH']
def place(e, center=CENTER, rot=(0, 0, 0)):
    e.rotation_euler = rot; e.location = (0, 0, 0); bpy.context.view_layer.update()
    pts = [o.matrix_world @ V(c) for o in kids(e) for c in o.bound_box]
    mn = V((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    mx = V((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    e.location = center - (mn + mx) / 2; bpy.context.view_layer.update()
def show(*es):
    for e in (HAM, CHI):
        vis = e in es
        for o in [e] + list(e.children_recursive): o.hide_render = not vis

def render(path, name):
    if os.environ.get("DRY"): return
    if os.environ.get("BORDER"):     # BORDER="y0,y1" (0..1 from image bottom): render one band on the full canvas
        y0, y1 = (float(v) for v in os.environ["BORDER"].split(","))
        sc.render.use_border = True; sc.render.use_crop_to_border = False
        sc.render.border_min_x, sc.render.border_max_x = 0.0, 1.0
        sc.render.border_min_y, sc.render.border_max_y = y0, y1
    sc.render.filepath = path; bpy.ops.render.render(write_still=True); print("RENDERED", name, flush=True)

def shoot(name, direction, target=None, size=None, objs=None, lens=85, tool="H"):
    path = f"{PRE}_{name}.png"
    if os.path.exists(path) and not FORCE: print("SKIP", name); return
    d = V(direction).normalized(); target = V(target) if target else None
    CAM.data.lens = lens; CAM.data.type = 'PERSP'; CAM.data.clip_start = 0.005
    rot = (-d).to_track_quat('-Z', 'Y')
    if target is None or size is None:
        pts = [o.matrix_world @ V(c) for o in objs for c in o.bound_box]
        if target is None: target = sum(pts, V()) / len(pts)
        R = rot.to_matrix(); right, upv = R.col[0], R.col[1]
        pr = [(p - target).dot(right) for p in pts]; pu = [(p - target).dot(upv) for p in pts]
        target = target + right * (min(pr) + max(pr)) / 2 + upv * (min(pu) + max(pu)) / 2
        if size is None: size = max(max(pr) - min(pr), max(pu) - min(pu))
    fov = 2 * math.atan(18 / lens)
    dist = (size / 2 * 1.12) / math.tan(fov / 2) + size * 0.3
    CAM.location = target + d * dist; CAM.rotation_euler = rot.to_euler()
    print("CAMDBG", name, round(size, 3), round(dist, 3), tuple(round(x, 3) for x in target), flush=True)
    build_rig(d, target, tool); render(path, name)

PROFILE_PAD = 0.07
KEYPTS = {"HP": {"striking_face_center": (-0.0603, 0, 0.295), "striking_face_center_alt": (0.0603, 0, 0.295),
                 "handle_pivot_grip_end": (0, 0, 0), "grip_center": (0, 0, 0.0935), "head_center": (0, 0, 0.295)},
          "CP": {"striking_top_center": (0, 0, 0.2403), "blade_tip": (0, 0, 0)}}

def shoot_profile(name, ent, kind, long_px):
    from bpy_extras.object_utils import world_to_camera_view
    path = f"{PRE}_{name}.png"
    pts = [o.matrix_world @ V(c) for o in kids(ent) for c in o.bound_box]
    x0, x1 = min(p.x for p in pts), max(p.x for p in pts); z0, z1 = min(p.z for p in pts), max(p.z for p in pts)
    y0 = min(p.y for p in pts)
    L = z1 - z0; pad = PROFILE_PAD * L; Hm = L + 2 * pad
    RX = int(round(long_px * (x1 - x0 + 2 * pad) / Hm / 2)) * 2; RY = long_px
    sc.render.resolution_x, sc.render.resolution_y = RX, RY
    CAM.data.type = 'ORTHO'; CAM.data.sensor_fit = 'AUTO'; CAM.data.ortho_scale = Hm
    CAM.data.clip_start = 0.01; CAM.data.clip_end = 10
    CAM.location = V(((x0 + x1) / 2, y0 - 1.0, (z0 + z1) / 2))
    CAM.rotation_euler = V((0, 1, 0)).to_track_quat('-Z', 'Y').to_euler(); bpy.context.view_layer.update()
    info = {"image": os.path.basename(path), "width": RX, "height": RY, "px_per_m": RY / Hm, "ortho_scale": Hm,
            "camera": "orthographic, looking +Y; image right = tool local +X (hammer) / blade-width axis seen edge-on (chisel)",
            "points_px": {}}
    for k, lp in KEYPTS[kind].items():
        w = ent.matrix_world @ V(lp); u = world_to_camera_view(sc, CAM, w)
        info["points_px"][k] = [round(u.x * RX, 1), round((1 - u.y) * RY, 1)]
    print("PROFILE", name, RX, RY, round(Hm, 5), info["points_px"], flush=True)
    jp = f"{PRE}_{name}.json"
    if not os.path.exists(jp) or FORCE: json.dump(info, open(jp, "w"), indent=1)
    if os.path.exists(path) and not FORCE: print("SKIP", name); return
    build_rig(V((0, -1, 0)), V(((x0 + x1) / 2, 0, (z0 + z1) / 2)), "H" if kind == "HP" else "C")
    render(path, name)

views = {"hammer_site": "H", "chisel_site": "C", "hammer_profile": "HP", "chisel_profile": "CP"}
names = list(views) if want == "all" else want.split(",")
if any(views[n] in ("HP", "CP") for n in names) and any(views[n] not in ("HP", "CP") for n in names):
    raise SystemExit("render profile views in a separate run")
print("PARAMS", json.dumps(P), flush=True)
for n in names:
    kind = views[n]
    if kind == "H": show(HAM); place(HAM); shoot(n, (0.62, -0.72, 0.30), objs=kids(HAM))
    elif kind == "C": show(CHI); place(CHI); shoot(n, (0.62, -0.72, 0.30), objs=kids(CHI), tool="C")
    else:
        ent = HAM if kind == "HP" else CHI; show(ent)
        place(ent, rot=(0, 0, 0) if kind == "HP" else (0, 0, math.pi / 2))
        shoot_profile(n, ent, kind, RES)
print("DONE")
