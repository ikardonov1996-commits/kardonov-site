# KARDONOV carving stages: hero rev7 (variant 25) light adapted to the 5 site stages.
# Same camera + same light for all stages (only the visible object changes) -> stills stack pixel-exact.
# usage (build work file from the ASSET; asset is never saved):
#   blender -b assets/anim_carving.blend -P scripts/stages_light/stages_light.py -- build
# render (resumable, skips existing, writes .part then renames):
#   blender -b out/stages_light/stages_work.blend -P scripts/stages_light/stages_light.py -- render OUTDIR W H SPP [stages e.g. 1,2,3]
#   env NSTRIP=4 (horizontal strips per still, each resumable; stitched to OUTDIR/stage_i.png), LIGHT_OVR=...
import bpy, sys, os, math
from mathutils import Vector as V
S = "/tmp/claude-0/-home-user-kardonov-site/cb30cd45-1b88-5b9b-b3ff-480343f6cfce/scratchpad"
WORK = f"{S}/out/stages_light/stages_work.blend"
D = bpy.data; sc = bpy.context.scene; O = D.objects
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []

ALL = ["Marble_Block", "C1_Pitched", "C3_Relief2", "C4_Freed", "C5_Point", "C6_Claw", "Sculpture_HiRes"]
SITE = ["Marble_Block", "C4_Freed", "C5_Point", "C6_Claw", "Sculpture_HiRes"]   # site stages 1..5
BLUE = (0.0, 0.443, 1.0)            # brand blue (AgX-compensated, brand_recolor.py) = hero RimBlueR colour
# --- hero variant 25 (rev7) values. az: deg from front (-Y) towards +X; camera sits at az ~+20.6 (3/4 from +X).
# Hero geometry is kept RELATIVE TO THE CAMERA and mirrored (hero cam az 20: key +68, sky -10, champ rim +110, blue rim
# -150 from the camera) -> here (cam az +20.6): key az -48 (viewer's upper left/front); sky, champagne rim and blue rim tuned below;
# blue rim on the opposite back side (grazes only the silhouette, never floods the +X face the camera sees).
EXPOSURE = -0.8; LOOK = "AgX - Medium High Contrast"; WORLD = 0.0006; AMB = (1.0, 0.97, 0.93)
T = (0.0, 0.0, 0.55)                # stage objects are ~1.0-1.17 m tall (hero tgt .66 on a taller figure)
# draft iteration (look_a..d): key tint (1,.73,.40) gave sandy/tan marble here (lit sat .22-.35; this marble base is
# creamier than the hero's) -> (1,.80,.55) = lit sat .13-.20, h31-32 (hero rev7 result h34 s.14); sky 40->55 W az 50 keeps
# half-tones ivory; champagne rim behind the key side 55->40 W (lit the block's left face head-on); blue rim az 170->178,
# el 28 (at 170 it flooded the block's +X face: 18% blue px). Draft v1 review: brand BLUE 150 W gave a saturated cyan
# patch on the back of the hip/drape (stages 3-5) -> #77D9FF-family colour, 80 W, from higher (el 38) aimed at z .78.
RIMCOL = (0.18, 0.69, 1.0)          # sRGB #77D9FF -> linear
LIGHTS = [
    dict(n="KeyWarm",  col=(1.0, 0.80, 0.55), e=92,  shape='DISK', size=1.4, az=-48, el=34, d=2.2, tgt=(0, 0, 0.62), spec=0.5),
    dict(n="Skylight", col=(1.0, 0.95, 0.90), e=55,  shape='DISK', size=1.2, az=50, el=78, d=2.3, tgt=(0, 0, 0.55), spec=0.4),
    dict(n="RimChamp", col=(1.0, 0.72, 0.42), e=40,  shape='RECTANGLE', size=0.12, size_y=1.6, az=-115, el=10, d=2.0, tgt=(-0.02, 0, 0.55), spec=0.35),
    dict(n="RimBlue",  col=RIMCOL,            e=80,  shape='RECTANGLE', size=0.12, size_y=1.1, az=178, el=38, d=2.0, tgt=(0.02, 0, 0.78), spec=0.35),
    dict(n="Bounce",   col=(1.0, 0.95, 0.90), e=0.5, shape='DISK', size=2.0, az=0, el=-28, d=2.5, tgt=(0, 0, 0.55), shadow=False),
    # v3 (client on v2: the wide front fill flattened the bodies; the block's +X face read near-black next to the
    # statues' shadow sides):
    # HeadFill = small soft SPOT aimed at the face/hairline only (cone 14 deg + blend, radius 8 cm -> soft shadows),
    # light-linked to the figure stages: lifts the near-black pocket under the hair/brow, the body keeps v1 depth.
    dict(n="HeadFill", typ='SPOT', col=(1.0, 0.96, 0.92), e=10, radius=0.08, cone=14, blend=0.6, az=35, el=12, d=1.2,
         tgt=(0.005, -0.045, 0.90), link="FIG"),
    # SideFill = broad neutral soft fill from the camera-right side for ALL stages (same balance for block and figures):
    # the block's +X face and the statues' shadow sides read deep but with detail.
    # look_v3a: 10 W -> block +X face lum 38 -> 81 (flat), statue body p10 56 -> 73; 4 W targets ~55-60 = v1 statue shadow side.
    dict(n="SideFill", col=(1.0, 0.97, 0.94), e=4,  shape='DISK', size=2.5, az=100, el=20, d=2.5, tgt=(0, 0, 0.55), spec=0.2),
]
FIG = ["C4_Freed", "C5_Point", "C6_Claw", "Sculpture_HiRes"]
OVR = os.environ.get("LIGHT_OVR")      # e.g. LIGHT_OVR="RimBlue.e=90,KeyWarm.col=1/.8/.55,EXPOSURE=-0.7"
if OVR:
    for kv in OVR.split(","):
        k, v = kv.split("=")
        if "." in k:
            n, a = k.split(".")
            for L in LIGHTS:
                if L["n"] == n: L[a] = tuple(float(x) for x in v.split("/")) if "/" in v else float(v)
        else: globals()[k] = float(v)

def place_dir(tgt, az, el, d):
    a, e = math.radians(az), math.radians(el)
    return V(tgt) + d * V((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))

def build_light():
    c = D.collections.get("STAGE_LIGHT")
    if c is None: c = D.collections.new("STAGE_LIGHT"); sc.collection.children.link(c)
    for o in list(c.objects): D.objects.remove(o, do_unlink=True)
    for n in ("Key", "Fill", "Rim"):                       # old 3-point rig off
        if n in O: O[n].hide_render = True; O[n].hide_viewport = True
    def mk(name, L, e):
        if L.get("typ") == 'SPOT':
            ld = D.lights.new(name, 'SPOT'); ld.color = L["col"]; ld.energy = e; ld.shadow_soft_size = L["radius"]
            ld.spot_size = math.radians(L["cone"]); ld.spot_blend = L["blend"]
        else:
            ld = D.lights.new(name, 'AREA'); ld.color = L["col"]; ld.energy = e; ld.shape = L["shape"]; ld.size = L["size"]
        if L.get("shape") == 'RECTANGLE': ld.size_y = L["size_y"]
        ld.use_shadow = L.get("shadow", True)
        if L.get("spread"): ld.spread = math.radians(L["spread"])      # area-light beam (Cycles)
        o = D.objects.new(name, ld); c.objects.link(o); o.location = place_dir(L["tgt"], L["az"], L["el"], L["d"])
        o.rotation_euler = (V(L["tgt"]) - o.location).to_track_quat('-Z', 'Y').to_euler(); o.visible_camera = False
        return o
    def link(o, L):
        if not L.get("link"): return
        rc = D.collections.get("SL_LINK_" + L["link"])
        if rc is None:
            rc = D.collections.new("SL_LINK_" + L["link"])
            for n in globals()[L["link"]]: rc.objects.link(O[n])
        o.light_linking.receiver_collection = rc
    for L in LIGHTS:
        if L["e"] <= 0: continue
        o = mk("SL_" + L["n"], L, L["e"]); link(o, L)
        sp = L.get("spec", 1.0)
        if sp < 1.0:     # Cycles ignores specular_factor: diffuse-only light + glossy-only twin at e*spec (as hero)
            o.visible_glossy = False
            t = mk("SL_" + L["n"] + "_spec", L, L["e"] * sp); link(t, L)
            t.visible_diffuse = False; t.visible_transmission = False; t.visible_volume_scatter = False
    # world: tiny neutral ambient (hero rev7: 0.0006 x (1,.97,.93)); camera never sees it (film transparent)
    w = sc.world; w.use_nodes = True; bg = w.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (*[x * WORLD for x in AMB], 1); bg.inputs["Strength"].default_value = 1.0
    vs = sc.view_settings; vs.view_transform = 'AgX'; vs.look = LOOK; vs.exposure = EXPOSURE; vs.gamma = 1.0
    sc.display_settings.display_device = 'sRGB'

def setup_cycles(spp):
    sc.render.engine = 'CYCLES'; C = sc.cycles; C.device = 'CPU'; C.samples = spp
    C.use_adaptive_sampling = True; C.adaptive_threshold = float(os.environ.get("ADAPT", "0.03")); C.adaptive_min_samples = 16
    C.use_denoising = True; C.denoiser = 'OPENIMAGEDENOISE'; C.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
    C.denoising_prefilter = 'ACCURATE'
    C.max_bounces = 6; C.diffuse_bounces = 1; C.glossy_bounces = 2; C.transmission_bounces = 2
    C.transparent_max_bounces = 8; C.caustics_reflective = False; C.caustics_refractive = False
    C.use_light_tree = True; C.sample_clamp_indirect = 10.0
    sc.render.film_transparent = True; sc.render.use_persistent_data = True
    sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'
    sc.render.image_settings.color_depth = '8'
    O["Floor"].is_shadow_catcher = True            # as render_stills.py

import time
T0 = time.time(); BUDGET = float(os.environ.get("BUDGET", "455"))   # s per blender run (chain uses timeout 470)
NSTRIP = int(os.environ.get("NSTRIP", "4")); PAD = 16      # horizontal strips (border render), overlap PAD px

def assemble(out, i, w, h):
    """stitch strip PNGs (each full-frame RGBA, only its band rendered) -> stage_i.png. Pure Blender (no PIL needed)."""
    import numpy as np
    acc = np.zeros((h, w, 4), np.float32)
    for k in range(NSTRIP):
        im = D.images.load(f"{out}/parts/stage_{i}_s{k}.png"); a = np.array(im.pixels[:], np.float32).reshape(h, w, 4)
        y0, y1 = k * h // NSTRIP, (k + 1) * h // NSTRIP          # rows from bottom (Blender pixel order)
        acc[y0:y1] = a[y0:y1]; D.images.remove(im)
    img = D.images.new(f"stage_{i}", w, h, alpha=True); img.alpha_mode = 'STRAIGHT'
    img.pixels = acc.ravel(); img.filepath_raw = f"{out}/stage_{i}.part.png"; img.file_format = 'PNG'; img.save()
    os.replace(f"{out}/stage_{i}.part.png", f"{out}/stage_{i}.png"); D.images.remove(img)

def render(out, w, h, spp, only):
    os.makedirs(f"{out}/parts", exist_ok=True)
    build_light(); setup_cycles(spp)
    r = sc.render; r.resolution_x = w; r.resolution_y = h; r.resolution_percentage = 100
    r.use_border = True; r.use_crop_to_border = False
    frames = list(sc["stage_frames"])
    for i in only:
        n = SITE[i - 1]; fn = f"{out}/stage_{i}.png"
        if os.path.exists(fn): print("STILL exists", fn, flush=True); continue
        sc.frame_set(frames[ALL.index(n)])
        for m in ALL: O[m].hide_render = (m != n)
        for k in range(NSTRIP):
            pf = f"{out}/parts/stage_{i}_s{k}.png"
            if os.path.exists(pf): continue
            est = float(os.environ.get("STRIP_EST", "0")) or getattr(render, "last", 0.0)
            if est and time.time() - T0 + 1.15 * est > BUDGET:
                print("STRIP budget: stop before", i, k, "(next run continues)", flush=True); return
            t1 = time.time()
            y0, y1 = k * h // NSTRIP, (k + 1) * h // NSTRIP          # border y is from the bottom
            r.border_min_x, r.border_max_x = 0.0, 1.0
            r.border_min_y = max(0, y0 - PAD) / h; r.border_max_y = min(h, y1 + PAD) / h
            tmp = f"{out}/parts/stage_{i}_s{k}.part.png"; r.filepath = tmp
            bpy.ops.render.render(write_still=True); os.replace(tmp, pf)
            render.last = time.time() - t1; print("STRIP", i, k, "%.0fs" % render.last, flush=True)
        assemble(out, i, w, h); print("STILL", i, n, fn, flush=True)

if argv and argv[0] == "build":
    build_light(); setup_cycles(64)
    os.makedirs(os.path.dirname(WORK), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=WORK, copy=True); print("SAVED", WORK)
elif argv and argv[0] == "headtest":      # -- headtest OUT.png STAGE  (head crop of the 1080x1440 frame, 64 spp)
    out, i = argv[1], int(argv[2]); build_light(); setup_cycles(64); r = sc.render
    r.resolution_x, r.resolution_y, r.resolution_percentage = 1080, 1440, 100
    r.use_border = True; r.use_crop_to_border = True
    r.border_min_x, r.border_max_x, r.border_min_y, r.border_max_y = 0.37, 0.56, 0.655, 0.79
    n = SITE[i - 1]; sc.frame_set(list(sc["stage_frames"])[ALL.index(n)])
    for m in ALL: O[m].hide_render = (m != n)
    r.filepath = out; bpy.ops.render.render(write_still=True); print("HEAD", out, flush=True)
elif argv and argv[0] == "render":
    out, w, h, spp = argv[1], int(argv[2]), int(argv[3]), int(argv[4])
    only = [int(x) for x in argv[5].split(",")] if len(argv) > 5 else [1, 2, 3, 4, 5]
    render(out, w, h, spp, only)
