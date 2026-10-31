# HERO lighting/camera for the KARDONOV cyber-David.
# Usage (always from the ASSET; the asset is never saved, the scene is written to out/hero/hero_work.blend):
#   blender -b assets/asset_statue_cyber.blend -P scripts/hero/hero_light.py -- [render]
# env: VARIANT=1|2|3 (or "1,2,3")  SHOTS=A,B  ROT=0,10,-15 (orbit deg, +=CCW from above=towards human arm)
#     REBUILD: just run on the asset again (after the seam fix) -> hero_work.blend is rebuilt from scratch;  SCALE=1.0 (res multiplier)  SPP=16  FORCE=1  TAG=suffix
#      NOSAVE=1 (skip writing hero_work.blend)
# In hero_work.blend: collections HERO_V1/HERO_V2/HERO_V3 (variant rigs) + HERO_Practicals (headband/neon lights,
# shared). Switch: run set_variant(n) from this file, or toggle collection "exclude" in the outliner (one V on).
# Output per shot/variant (resumable, skip if exists): out/hero/layers/{shot}_v{n}_beauty.png (RGBA, transparent bg,
# real practical light baked in) and {shot}_v{n}_glow.png (RGB-on-black halo from emission+AOV only).
# Preview composite on #0f0f12 is made by hero_post.py (system python, PIL).
import bpy, bmesh, sys, os, math
from mathutils import Vector as V

S = "/tmp/claude-0/-home-user-kardonov-site/cb30cd45-1b88-5b9b-b3ff-480343f6cfce/scratchpad"
OUT = f"{S}/out/hero"; LAY = f"{OUT}/layers"; os.makedirs(LAY, exist_ok=True)
D = bpy.data; sc = bpy.context.scene
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []

def lin(h):
    h = h.lstrip("#"); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)
sys.path.insert(0, f"{S}/scripts")
from brand_recolor import BLUE, CHAMP     # AgX-compensated brand colours (see brand_recolor.py)
AMBER = (0.985, 0.54, 0.115)    # headband practical light: champagne between AgX-compensated (1,.487,0) and plain
                                # sRGB->linear #FCCB84 -- the fully compensated colour turns orange on dim marble
COOL = (0.78, 0.86, 1.0)
def mixw(c, k): return tuple(x * k + (1 - k) for x in c)   # brand colour at saturation k (marble must stay marble)
CHAMP_K = mixw(CHAMP, 0.55)
# practical / spill light colour: plain sRGB->linear #FCCB84. At the low brightness of spill on marble the AgX-compensated
# (1,.487,0) displays orange-yellow (~#956500 at 0.3); the plain value displays ~#96713D = darker #FCCB84 hue.
CHAMP_LIGHT = (0.973, 0.597, 0.231)

# ---------------------------------------------------------------- variants
# az: degrees from front (-Y) towards the statue's LEFT (+X, human side); negative = robot side (-X). el: elevation.
VARIANTS = {
 1: dict(name="Chiaroscuro", exposure=0.0, look="AgX - Medium High Contrast", world=0.0012, prac=1.0,
     lights=[
      dict(n="Key", col=CHAMP_K, e=170, shape='DISK', size=0.55, az=68, el=42, d=2.4, tgt=(0.0, 0, 0.72), jitter=True),
      dict(n="RimBlue", col=BLUE, e=1500, shape='RECTANGLE', size=0.35, size_y=1.6, az=-155, el=25, d=2.0, tgt=(-0.06, 0, 0.58), jitter=True),
      dict(n="FillCool", col=COOL, e=5, shape='DISK', size=2.5, az=-35, el=8, d=3.2, tgt=(0, 0, 0.55), shadow=False),
     ]),
 # rev4 colour: key (1,.66,.42) [rev3 mixw(CHAMP,.6)], halo gain .12 [.35], band emission 1.0 [1.3], blue lights jittered.
 # rev3 (client): no ArmSpec (arm read glossy/glowing), larger softer keys (no hotspots), -0.3 EV, broad soft world
 # lift for the arm's shadow side, headband practical more visible (pale champagne), champagne-gold band metal.
 # rev2 was: exposure 0, prac .38, keys 0.45/0.5 m, softbox r16 s5, ArmSpec 130 W spec-only card.
 2: dict(name="Split", exposure=-0.6, look="AgX - Medium High Contrast", world=0.0028, prac=1.3, glow=0.12, band_emit=0.6, neon=2.5, neon_es=8.0, blue_glow=0.8, emit_glow=0.0,
     prac_col=(1.0, 0.72, 0.28),
     # absolute emission strengths for the headband (with HEAD_EMIT colour from brand_recolor: displays ~#F0C894
     # = closest reachable to #FCCB84 under AgX MHC -0.3 EV; at low strength the colour skews lemon-yellow)
     band_es={"Neuro_GlowAmber": 1.0, "Neuro_GlowRing": 1.0, "Neuro_Lens": 0.8},
     # soft round "softbox" patch in the WORLD (camera never sees it: film transparent): broad cool lift of the AI side
     # and a satin (not hotspot) reflection on the titanium.
     softbox=dict(az=-70, el=14, r=32, strength=3.0, col=mixw(BLUE, 0.45)),
     lights=[
      dict(n="KeyWarm", col=(1.0, 0.66, 0.42), e=140, shape='DISK', size=1.3, az=90, el=22, d=2.2, tgt=(0.0, 0, 0.65), jitter=True),
      dict(n="KeyBlue", col=BLUE, e=420, shape='DISK', size=1.0, az=-125, el=24, d=2.1, tgt=(-0.05, 0, 0.62), jitter=True, specular=0.4),   # rev3: spec x0.4 -> no hot rim streaks on the titanium
      # soft warm floor-bounce from below-front: lifts the deepest shadows (no crushed blacks), shadowless
      dict(n="Bounce", col=mixw(CHAMP_LIGHT, 0.5), e=5, shape='DISK', size=2.0, az=0, el=-28, d=2.5, tgt=(0, 0, 0.55), shadow=False),
     ]),
 3: dict(name="Museum top", exposure=0.0, look="AgX - Medium High Contrast", world=0.0015, prac=1.3,
     lights=[
      dict(n="Skylight", col=CHAMP_K, e=150, shape='DISK', size=1.6, az=8, el=78, d=2.3, tgt=(0.0, 0, 0.6), jitter=True),
      dict(n="RimBlueR", col=BLUE, e=900, shape='RECTANGLE', size=0.14, size_y=1.6, az=-128, el=10, d=2.0, tgt=(-0.02, 0, 0.55), jitter=True),
      dict(n="RimBlueL", col=BLUE, e=700, shape='RECTANGLE', size=0.14, size_y=1.6, az=128, el=10, d=2.0, tgt=(0.02, 0, 0.55), jitter=True),
     ]),
}

# v2.5 / "v6" = CLIENT-APPROVED light (rev4b, 2026-10-29; locked copy: hero_light_v6_approved.py). Do not change _v25
# defaults. Between t3-v2 (deep contrast, warm/blue split) and t3-v3 (top light modelling + thin blue rims).
IVORY = mixw(CHAMP, 0.42)        # (1, .78, .58): warm-ivory light, marble stays clean ivory
# rev4b: light specular factors < 1 so the metal arm is not glossy/bright (marble is mostly diffuse+SSS)
def _v25(name, exposure=-0.3, world=0.0015, sky=75, kblue=330, rimR=300, rimL=300, bounce=2.5, softbox=None, kwarm=150,
         ksize=0.6, neon=None, kbcol=None):
    d = dict(name=name, exposure=exposure, look="AgX - Medium High Contrast", world=world, prac=1.0, glow=0.12, band_emit=0.6,
             prac_col=(1.0, 0.72, 0.28), band_es={"Neuro_GlowAmber": 1.0, "Neuro_GlowRing": 1.0, "Neuro_Lens": 0.8},
             neon=5.0, neon_es=8.0, blue_glow=0.8, emit_glow=0.0, lights=[
      dict(n="KeyWarm", col=IVORY, e=kwarm, shape='DISK', size=ksize, az=88, el=34, d=2.2, tgt=(0.0, 0, 0.66), jitter=True, specular=0.5),
      dict(n="Skylight", col=mixw(CHAMP, 0.25), e=sky, shape='DISK', size=1.2, az=10, el=78, d=2.3, tgt=(0.0, 0, 0.6), jitter=True, specular=0.4),
      dict(n="KeyBlue", col=kbcol or BLUE, e=kblue, shape='DISK', size=0.5, az=-125, el=24, d=2.1, tgt=(-0.05, 0, 0.62), jitter=True, specular=0.2),
      dict(n="RimBlueR", col=BLUE, e=rimR, shape='RECTANGLE', size=0.12, size_y=1.6, az=-130, el=10, d=2.0, tgt=(-0.02, 0, 0.55), jitter=True, specular=0.35),
      dict(n="RimBlueL", col=BLUE, e=rimL, shape='RECTANGLE', size=0.12, size_y=1.6, az=130, el=10, d=2.0, tgt=(0.02, 0, 0.55), jitter=True, specular=0.35),
      dict(n="Bounce", col=mixw(CHAMP_LIGHT, 0.4), e=bounce, shape='DISK', size=2.0, az=0, el=-28, d=2.5, tgt=(0, 0, 0.55), shadow=False),
    ])
    if softbox: d["softbox"] = softbox
    if neon: d.update(neon)          # neon practical overrides (rig lights untouched)
    return d
VARIANTS[6] = _v25("v6 = v2.5 approved (rev4b)")
VARIANTS[7] = _v25("v2.5 more contrast", world=0.0008, sky=55, kblue=220, rimR=200, rimL=220, bounce=0.0)
VARIANTS[8] = _v25("v2.5 brighter", exposure=-0.15, world=0.003, sky=100, bounce=4.0,
                   softbox=dict(az=-70, el=14, r=32, strength=1.5, col=(0.9, 0.93, 1.0)))
# rev5 neon (client: indicators must read as light sources with soft blue spill, aligned): brighter/whiter emitter core,
# moderate point energy with a soft radius (saturated #77D9FF spill, not a white blow-out), tighter + stronger halo.
NEON5 = dict(neon=7.0, neon_soft=0.005, neon_es=14.0, blue_glow=2.0, neon_core=0.35)
# v6c: v6 nudged towards t3-v2 -- deeper shadows / stronger form (weaker top+bounce+world, slightly crisper key, a bit
# more blue key), same ivory key colour, same headband, same exposure family.
# rev5b (client on E_v6 probe: "usable, slightly deeper; no face/fist hotspots, face max <=~235"): -0.35 EV, bigger key
# (softer roll-off), less top/bounce/world fill (higher key:fill), a bit more blue key. (rev5a was exp -0.25, world
# .0009, sky 45, kblue 400, bounce 1.0, key .5 m 160 W.)
VARIANTS[9] = _v25("v6c (v6 deeper, t3-v2 direction)", exposure=-0.6, world=0.0010, sky=50, kblue=380, bounce=1.0,
                   ksize=0.9, kwarm=130, neon=NEON5)     # rev5b probe: exp -.65/key 165 -> face >=240 4.7% -> key down
VARIANTS[10] = _v25("v6 + rev5 neon", neon=NEON5)
# v11 "arm": v6 family for the robot-arm views (client/lead: external cold blue flooded the arm, neon read as overexposure).
# Darker overall, blue key almost off, robot-side blue rim thin+weak (silhouette only), titanium lit by the ivory key and
# its own neon; neon spill limited to a few cm (custom light distance), whiter/stronger emitter core.
NEON_ARM = dict(neon=6.0, neon_soft=0.003, neon_dist=0.035, neon_es=18.0, blue_glow=2.6, neon_core=0.45)
# rev6 LEDs (client: the 3 forearm dots merged into one blob). Cause: their point lights sat 3 mm off the dot ALONG +Z
# (closed dot meshes -> area-weighted normal = 0 -> fallback (0,0,1)), 72 mW each, 3.5 cm reach vs 8 mm dot spacing ->
# three overlapping ~2 cm spill pools = one blob. Fix (runtime, fix_leds): each dot's light ON its real outward normal,
# 0.8 mm above the face, tight radius, reach < half the spacing; weaker dot emission + smaller halo; a faint shared spill.
# led = [e_W, reach_m, soft_m, off_m(above face), dot_es, dot_halo(AOV x), spill_e_W, spill_reach_m]
NEON_ARM["led"] = [0.010, 0.0038, 0.0006, 0.0008, 9.0, 0.6, 0.004, 0.02]
# rev5c (solo-light diag D -35: blue key + robot rim gave 3x the neon's blue on arm/marble): "KeyBlue" becomes a weak
# NEUTRAL cool-white side key (titanium stays readable, no saturated blue), robot rim 18 W = silhouette only.
VARIANTS[11] = _v25("v6 arm (neon-led)", exposure=-0.55, world=0.0009, sky=45, kblue=110, kbcol=(0.86, 0.9, 1.0), rimR=18, rimL=160, bounce=1.5,
                    neon=NEON_ARM)
_ARM = dict(world=0.0009, kbcol=(0.86, 0.9, 1.0), rimR=18, rimL=160, neon=NEON_ARM)
VARIANTS[12] = _v25("v6 arm - more contrast", exposure=-0.75, sky=30, kblue=70, bounce=0.6, **_ARM)
VARIANTS[13] = _v25("v6 arm - slightly brighter", exposure=-0.35, sky=55, kblue=140, bounce=2.0, **_ARM)

# ---------------------------------------------------------------- rev6 (CYCLES drafts)
# Client rev6: (1) LEDs/neon must EMIT (own small pools), (2) all neon lit-upon -> Cycles: emissive meshes are the real
# light sources, every fake PR_Neon*/PR_LedSpill point light is OFF; (3) blue on the FAR (human) side was RimBlueL
# (BLUE, az +130 = behind the HUMAN shoulder) + KeyBlue's wrap over the neck -> RimL becomes a champagne rim, KeyBlue
# moved more to the robot side/behind and narrowed; (4) more champagne key (hue ~35, sat ~.45 on lit marble).
# cy = Cycles-only settings: es = neon emission strength (W/m2-ish, shared glow mats), led_es = forearm dots, hot = shoulder
# emitter (Cyber_GlowBlueHot) strength, core = whitening of the emitter colour, band = headband PR light x, band_es x,
# rimLcol = colour of the human-side rim, kb = (az, el, size) of KeyBlue, gi = (diffuse, glossy) bounces.
CHAMP_KEY = (1.0, 0.70, 0.40)       # rev6 warm key: displays ~#E9C79A..#FCCB84-ish on lit marble under AgX MHC
def _v6r(name, base, **cy):
    d = dict(VARIANTS[base]); d["name"] = name; d["engine"] = "CYCLES"
    c = dict(es=220.0, hot=220.0, sh_glow=1.4, sh_sig=0.0105, sh_pw=3.0, blue_glow=0.6, blue_size=6, led_halo=0.25, line_es=60.0, core=0.0, band=2.5, band_es=1.8, glow=0.26, gi_d=1, led_es=1200.0, pad=(0.62, 0.1, 0.45, 8.0, 0.0021, 3.0), kwarm_col=CHAMP_KEY, kwarm=None,
             rimL=110, rimLcol=(1.0, 0.72, 0.42), kb=(-150, 12, 0.5), kblue=None, rimR=None, sky=None, bounce=None,
             exposure=None, world=None)
    c.update(cy); d["cy"] = c; d["led"] = list(NEON_ARM["led"])     # forearm dots get their own material
    L = []
    for l in d["lights"]:
        l = dict(l)
        if l["n"] == "KeyWarm":
            l["col"] = c["kwarm_col"]
            if c.get("ksize"): l["size"] = c["ksize"]
            if c["kwarm"] is not None: l["e"] = c["kwarm"]
        if l["n"] == "RimBlueL":
            l["n"] = "RimChampL"; l["col"] = c["rimLcol"]; l["e"] = c["rimL"]
        if l["n"] == "KeyBlue":
            l["az"], l["el"], l["size"] = c["kb"]
            if c.get("kb_tz"): l["tgt"] = (c.get("kb_tx", l["tgt"][0]), l["tgt"][1], c["kb_tz"])
            if c["kblue"] is not None: l["e"] = c["kblue"]
        if l["n"] == "RimBlueR" and c["rimR"] is not None: l["e"] = c["rimR"]
        if l["n"] == "RimBlueR" and c.get("rimR_box"):      # rev7c: shorter + aimed higher (kept off the legs/drape)
            l["size_y"], tz = c["rimR_box"]; l["tgt"] = (l["tgt"][0], l["tgt"][1], tz)
        if l["n"] == "RimBlueR" and c.get("rimR_dir"): l["az"], l["el"] = c["rimR_dir"]   # final: (az, el)
        if l["n"] == "Skylight" and c["sky"] is not None: l["e"] = c["sky"]
        if l["n"] == "Bounce" and c["bounce"] is not None: l["e"] = c["bounce"]
        if l["n"] == "Skylight" and c.get("skycol"): l["col"] = c["skycol"]
        if l["n"] == "Bounce" and c.get("bouncecol"): l["col"] = c["bouncecol"]
        L.append(l)
    d["lights"] = L
    if c["exposure"] is not None: d["exposure"] = c["exposure"]
    if c["world"] is not None: d["world"] = c["world"]
    return d
# lead review (c4): champagne overshot (sandy/tan marble) -> softer key tint (lit marble sat ~.3), neutral ivory top/bounce
# fill so the half-tones stay clean ivory (was kwarm_col (1,.58,.14), warm sky/bounce).
# client (hotspots on the human side: face/temple under the headband, deltoid/biceps/forearm edge): key 130->100 W and
# 0.9->1.4 m (softer roll-off), champagne rim 110->55 W, headband PR lights x2.5->x1.8 (halo AOV up instead), robot rim 300->220.
VARIANTS[14] = _v6r("rev6 v6c CYCLES (main)", 9, exposure=-0.8, bounce=0.5, sky=40, world=0.0006, kwarm_col=(1.0, 0.71, 0.40),
                    skycol=(1.0, 0.95, 0.90), bouncecol=(1.0, 0.95, 0.90), kwarm=100, ksize=1.4, rimL=55, band=1.8, glow=0.32,
                    rimR=220)
# rev7 (client on rev6): accent line removed, shoulder disc with readable rings, neutral ambient, KeyBlue narrower and
# more to the robot side (only rims it), champagne key towards h35.
_R7 = dict(no_accent=True, elbow_es=90.0, sh_rings=(80.0, 30.0, 3.0, 35.0, 0.0062), ambcol=(1.0, 0.97, 0.93), kb=(-140, 14, 0.3),
           kwarm_col=(1.0, 0.73, 0.40), skycol=(1.0, 0.95, 0.90), bouncecol=(1.0, 0.95, 0.90))
# rev7b: KeyBlue back to a rim (-118 lit the robot-side front too much), key 100->92 W (human arm max 244 at E-45)
VARIANTS[25] = _v6r("rev7 main (v14 + rev7 fixes)", 9, exposure=-0.8, bounce=0.5, sky=40, world=0.0006, kwarm=92, ksize=1.4,
                    rimL=55, band=1.8, glow=0.32, rimR=130, kblue=220, rimR_box=(0.8, 0.72), **_R7)
# rev7d: robot-side rim was a continuous neon-like line along the arm silhouette -> rim 220->130 W, KeyBlue 300->220 W
# rev7c: residual cold strip on the back drape between the legs in A = RimBlueR (1.6 m tall, aimed at z .55) -> 0.8 m, z .72
# final (client approved rev7; A: faint cold strip on the back drape between the legs = low robot-side rims passing
# between the legs) -> lab 27/28: rims from higher up so they only catch the robot-side silhouette.
_V25 = dict(exposure=-0.8, bounce=0.5, sky=40, world=0.0006, kwarm=92, ksize=1.4, rimL=55, band=1.8, glow=0.32, rimR=130, **_R7)
VARIANTS[27] = _v6r("final lab: rims higher", 9, kblue=220, rimR_box=(0.8, 0.72), rimR_dir=(-130, 35),
                    **{**_V25, "kb": (-140, 32, 0.3)})
VARIANTS[28] = _v6r("final lab: rims higher + shorter", 9, kblue=220, rimR_box=(0.55, 0.80), rimR_dir=(-120, 40),
                    **{**_V25, "kb": (-135, 38, 0.3)})
VARIANTS[32] = _v6r("final lab: blue spread 30", 9, kblue=220, rimR_box=(0.8, 0.72), blue_spread=30.0, **_V25)
VARIANTS[33] = _v6r("final lab: blue spread 18", 9, kblue=220, rimR_box=(0.8, 0.72), blue_spread=18.0, **_V25)
VARIANTS[34] = _v6r("final: v25 + KeyBlue robot-only + rim spread 18", 9, kblue=220, rimR_box=(0.8, 0.72), blue_spread=18.0,
                    kb_robot_only=True, **_V25)
VARIANTS[35] = _v6r("final lab: KeyBlue beam aimed at the arm/shoulder", 9, kblue=220, rimR_box=(0.8, 0.72), blue_spread=14.0,
                    kb_tz=0.78, **_V25)
VARIANTS[36] = _v6r("final lab: KeyBlue beam higher + rim spread 10", 9, kblue=220, rimR_box=(0.7, 0.78), blue_spread=10.0,
                    kb_tz=0.85, **_V25)
# (area-light spread keeps the power -> a narrow beam gets much brighter: hot robot plates; not used)
VARIANTS[37] = _v6r("final lab: KeyBlue aimed at the upper arm (no spread)", 9, kblue=220, rimR_box=(0.8, 0.72),
                    kb_tz=0.80, kb_tx=-0.12, **_V25)
VARIANTS[38] = _v6r("final lab: KeyBlue aimed higher + rim higher (no spread)", 9, kblue=220, rimR_box=(0.6, 0.80),
                    kb_tz=0.88, kb_tx=-0.12, **_V25)
VARIANTS[39] = _v6r("final lab: blue beams spread 14, energy x0.15", 9, kblue=33, rimR_box=(0.8, 0.72), blue_spread=14.0,
                    kb_tz=0.78, **{**_V25, "rimR": 20})
VARIANTS[40] = _v6r("final lab: blue beams spread 14, energy x0.3", 9, kblue=66, rimR_box=(0.8, 0.72), blue_spread=14.0,
                    kb_tz=0.78, **{**_V25, "rimR": 39})
VARIANTS[41] = _v6r("final lab: blue beams spread 14, energy x0.08", 9, kblue=18, rimR_box=(0.8, 0.72), blue_spread=14.0,
                    kb_tz=0.74, **{**_V25, "rimR": 11})
# FINAL light (client-approved rev7 + A back-drape fix): variant 42. KeyBlue = narrow beam (spread 14 deg; spread keeps
# the power, hence 18 W) aimed at the arm/upper torso (z .74), robot rim plain 90 W -> blue in A's deep shadows 5.8% -> 0.1%.
VARIANTS[42] = _v6r("final lab: KeyBlue beam (spread 14, 18 W) + plain rim 90 W", 9, kblue=18, rimR_box=(0.8, 0.72),
                    blue_spread=14.0, rim_spread=180.0, kb_tz=0.74, **{**_V25, "rimR": 90})
VARIANTS[43] = _v6r("final lab: KeyBlue beam (spread 14, 12 W) + plain rim 60 W", 9, kblue=12, rimR_box=(0.8, 0.72),
                    blue_spread=14.0, rim_spread=180.0, kb_tz=0.74, **{**_V25, "rimR": 60})
VARIANTS[29] = _v6r("diag: v25, KeyBlue off", 9, kblue=0, rimR_box=(0.8, 0.72), **_V25)
VARIANTS[30] = _v6r("diag: v25, RimBlueR off", 9, kblue=220, rimR_box=(0.8, 0.72), **{**_V25, "rimR": 0})
VARIANTS[31] = _v6r("diag: v25, both blue off", 9, kblue=0, rimR_box=(0.8, 0.72), **{**_V25, "rimR": 0})
VARIANTS[26] = _v6r("rev7 arm (v15 + rev7 fixes)", 11, kwarm=115, ksize=1.0, rimL=55, **_R7)
VARIANTS[16] = _v6r("rev6 v6c CYCLES alt (more champagne, 1 GI bounce)", 9, exposure=-0.7, bounce=0.5, sky=35, world=0.0006,
                    kwarm_col=(1.0, 0.58, 0.14))
VARIANTS[15] = _v6r("rev6 v6-arm CYCLES (neon close-ups)", 11, kwarm=115, ksize=1.0, rimL=55, kwarm_col=(1.0, 0.71, 0.40), skycol=(1.0, 0.95, 0.90), bouncecol=(1.0, 0.95, 0.90))
VARIANTS[17] = _v6r("lab: v15 LEDs 2500", 11, led_es=2500.0)
VARIANTS[18] = _v6r("lab: v15 LEDs 4500", 11, led_es=4500.0)
VARIANTS[19] = _v6r("lab: v15 LEDs 2500, stronger/wider guide glow", 11, led_es=2500.0, pad=(0.55, 0.15, 0.42, 12.0, 0.003))
VARIANTS[20] = _v6r("lab: v15 LEDs 1200, guide glow 14/3.2mm", 11, led_es=1200.0, pad=(0.62, 0.1, 0.45, 14.0, 0.0032))
VARIANTS[21] = _v6r("lab: v15 LEDs 1800, guide glow 20/2.8mm", 11, led_es=1800.0, pad=(0.62, 0.1, 0.45, 20.0, 0.0028))
VARIANTS[22] = _v6r("lab: LEDs 1800, film glow 3/3.5mm", 11, led_es=1800.0, pad=(0.62, 0.1, 0.45, 3.0, 0.0035))
VARIANTS[23] = _v6r("lab: LEDs 1200, crisp film 8/2.1mm p3", 11, pad=(0.62, 0.1, 0.45, 8.0, 0.0021, 3.0))
VARIANTS[24] = _v6r("lab: LEDs 1200, crisp film 10/2.4mm p4", 11, pad=(0.62, 0.1, 0.45, 10.0, 0.0024, 4.0))

# rev4 light setups for the arm study (same keys as V2 where not stated)
_V2 = VARIANTS[2]
_COMMON = dict(look=_V2["look"], prac=_V2["prac"], glow=_V2["glow"], band_emit=_V2["band_emit"], prac_col=_V2["prac_col"],
               band_es=_V2["band_es"], emit_glow=0.0)
VARIANTS[4] = dict(name="Moody (warm key only, weak blue rim, arm lit by its own neon)", exposure=-0.6, world=0.0010,
    neon=5.0, neon_es=9.0, blue_glow=1.0, **_COMMON, lights=[
      dict(n="KeyWarm", col=(1.0, 0.66, 0.42), e=140, shape='DISK', size=1.3, az=90, el=22, d=2.2, tgt=(0.0, 0, 0.65), jitter=True),
      dict(n="RimBlue", col=BLUE, e=110, shape='RECTANGLE', size=0.2, size_y=1.4, az=-150, el=20, d=2.0, tgt=(-0.06, 0, 0.58), jitter=True, specular=0.4),
      dict(n="Bounce", col=mixw(CHAMP_LIGHT, 0.5), e=2, shape='DISK', size=2.0, az=0, el=-28, d=2.5, tgt=(0, 0, 0.55), shadow=False),
    ])
VARIANTS[5] = dict(name="Neutral studio key from the robot side", exposure=-0.6, world=0.0025,
    neon=2.5, neon_es=8.0, blue_glow=0.8, softbox=dict(az=-70, el=14, r=32, strength=1.5, col=(0.9, 0.93, 1.0)), **_COMMON, lights=[
      dict(n="KeyNeutral", col=(0.96, 0.96, 1.0), e=150, shape='DISK', size=1.3, az=-65, el=30, d=2.2, tgt=(-0.05, 0, 0.65), jitter=True),
      dict(n="FillWarm", col=(1.0, 0.66, 0.42), e=25, shape='DISK', size=1.5, az=95, el=15, d=2.3, tgt=(0.0, 0, 0.65), shadow=False),
      dict(n="Bounce", col=mixw(CHAMP_LIGHT, 0.5), e=4, shape='DISK', size=2.0, az=0, el=-28, d=2.5, tgt=(0, 0, 0.55), shadow=False),
    ])

# ---------------------------------------------------------------- shots
# A: full figure incl. pedestal, portrait 2:3. Camera at hip height (z 0.45 of a 0..0.994 statue = just below the
#    figure's mid-height), horizontal axis + lens shift (verticals stay parallel), 12 deg off-front to the statue's
#    left (shows the contrapposto + the turned face), 100 mm equiv, ~3.4 m -> head seen from slightly below.
# B: head + shoulders incl. headband and robotic shoulder, 3:2, 135 mm equiv, camera at chin/shoulder height, 20 deg
#    to the statue's left so the face (turned to his left) reads near-frontal.
SHOTS = {
 "A": dict(res=(800, 1200), az=12, d=3.40, cam_z=0.45, aim_xy=(0.02, 0.0), frame_z=0.497, lens=100, fit='VERTICAL'),
 # C: whole robotic arm, shoulder to hand (portrait); az 0 = pure front, use ROT<0 to look from the robot side
 "C": dict(res=(800, 1200), az=0, d=1.45, cam_z=0.60, aim_xy=(-0.16, 0.02), frame_z=0.615, lens=100, fit='VERTICAL'),
 # D: neon close-up, forearm + hand
 "D": dict(res=(800, 1200), az=0, d=0.80, cam_z=0.52, aim_xy=(-0.175, 0.0), frame_z=0.535, lens=100, fit='VERTICAL'),
 # E (rev5, client): close-up B re-framed 4:5 down to just below the elbows (robot elbow ring + start of forearm),
 #   head+headband at top with headroom (9:10); same 135 mm, az 20 = t3-v2 close-up turn (camera 20 deg to the statue's left).
 "E": dict(res=(1080, 1200), az=20, d=1.85, cam_z=0.84, aim_xy=(-0.03, 0.0), frame_z=0.7875, lens=135, fit='VERTICAL'),
 "B": dict(res=(1200, 800), az=20, d=1.85, cam_z=0.84, aim_xy=(-0.025, 0.0), frame_z=0.858, lens=135, fit='HORIZONTAL'),
}

def place_dir(tgt, az, el, d):
    a, e = math.radians(az), math.radians(el)
    return V(tgt) + d * V((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))

def aim(ob, tgt):
    ob.rotation_euler = (V(tgt) - ob.location).to_track_quat('-Z', 'Y').to_euler()

def coll(name, parent=None):
    c = D.collections.get(name)
    if c is None:
        c = D.collections.new(name); (parent or sc.collection).children.link(c)
    for o in list(c.objects): D.objects.remove(o, do_unlink=True)
    return c

def mk_light(c, name, ltype, col, e, loc, **kw):
    ld = D.lights.new(name, ltype); ld.color = col; ld.energy = e
    for k, v in kw.items(): setattr(ld, k, v)
    o = D.objects.new(name, ld); c.objects.link(o); o.location = loc; o.visible_camera = False
    return o

# ---------------------------------------------------------------- practicals (from the actual emitter geometry)
def ev_mesh(o):
    dg = bpy.context.evaluated_depsgraph_get(); me = o.evaluated_get(dg).to_mesh()
    bm = bmesh.new(); bm.from_mesh(me); bm.transform(o.matrix_world); return bm

def islands(bm, faces):
    fs = set(faces); seen = set(); out = []
    for f in faces:
        if f in seen: continue
        st = [f]; seen.add(f); comp = []
        while st:
            x = st.pop(); comp.append(x)
            for e in x.edges:
                for y in e.link_faces:
                    if y in fs and y not in seen: seen.add(y); st.append(y)
        A = sum(g.calc_area() for g in comp) or 1e-9
        c = sum((g.calc_center_median() * g.calc_area() for g in comp), V()) / A
        n = sum((g.normal * g.calc_area() for g in comp), V())
        if n.length < 0.3 * A:
            # rev6 fix: closed emitter islands (rings, dots, lamps) have ~zero area-weighted normal -> the old fallback
            # (0,0,1) put their lights 3 mm along +Z. Use the smallest-variance axis of the island (its facing) and
            # orient it outward = the side where a ray escapes from the surface.
            import numpy as np
            P = np.array([v.co[:] for g in comp for v in g.verts]); w, vec = np.linalg.eigh(np.cov((P - P.mean(0)).T))
            n = V(vec[:, 0])
            try:
                dg = bpy.context.evaluated_depsgraph_get()
                if sc.ray_cast(dg, c + n * 0.004, n)[0] and not sc.ray_cast(dg, c - n * 0.004, -n)[0]: n = -n
            except Exception: pass
        out.append((c, n.normalized() if n.length > 1e-9 else V((0, 0, 1)), A))
    return out

def build_practicals():
    c = coll("HERO_Practicals")
    # --- headband: 4 module lenses (stronger) + 12 points around the glow strip (weaker), all champagne-amber
    HC = V((-0.030, -0.003, 0.0))
    bm = ev_mesh(D.objects["Neuro_Modules_Glow"])
    for i, (p, n, A) in enumerate(islands(bm, list(bm.faces))):
        r = V((p.x - HC.x, p.y - HC.y, 0)).normalized()
        mk_light(c, f"PR_Mod{i}", 'POINT', AMBER, 0.020, p + r * 0.007, shadow_soft_size=0.004)
        # rev3: spill lights just above / below the band lips (the lips shadowed the centre lights -> forehead/hair)
        mk_light(c, f"PR_ModUp{i}", 'POINT', AMBER, 0.005, p + r * 0.020 + V((0, 0, 0.014)), shadow_soft_size=0.008)
        mk_light(c, f"PR_ModDn{i}", 'POINT', AMBER, 0.0025, p + r * 0.030 + V((0, 0, -0.008)), shadow_soft_size=0.012)
    bm.free()
    bm = ev_mesh(D.objects["Neuro_Band_Glow"]); bins = {}
    for v in bm.verts:
        a = math.atan2(v.co.y - HC.y, v.co.x - HC.x); k = int((a + math.pi) / (2 * math.pi) * 12) % 12
        bins.setdefault(k, []).append(v.co.copy())
    for k, pts in bins.items():
        p = sum(pts, V()) / len(pts); r = V((p.x - HC.x, p.y - HC.y, 0)).normalized()
        mk_light(c, f"PR_Band{k:02d}", 'POINT', AMBER, 0.006, p + r * 0.006, shadow_soft_size=0.004)
        mk_light(c, f"PR_BandUp{k:02d}", 'POINT', AMBER, 0.004, p + r * 0.006 + V((0, 0, 0.013)), shadow_soft_size=0.004)
        mk_light(c, f"PR_BandDn{k:02d}", 'POINT', AMBER, 0.005, p + r * 0.008 + V((0, 0, -0.013)), shadow_soft_size=0.004)
    bm.free()
    # --- arm neon: one small blue point per glow island (offset along its normal), accent line split in 3
    n_blue = 0
    GL = ("Cyber_GlowBlue", "Cyber_GlowBlueHot")
    for on, mats in (("Robo_Indicators", GL), ("Robo_Hand", GL), ("Robo_Mechanics", GL),
                     ("Robo_ShoulderEmitter_Glow", None), ("Robo_Glow_AccentUpper", None)):
        o = D.objects.get(on)
        if o is None: continue
        bm = ev_mesh(o)
        mi = [i for i, m in enumerate(o.data.materials) if m and (mats is None or m.name in mats)]
        fl = [f for f in bm.faces if f.material_index in mi]
        isl = islands(bm, fl)
        if not fl: bm.free(); continue
        if on == "Robo_Glow_AccentUpper":
            # the long accent line = a chain of thin RECTANGLE area lights lying ON the line, facing out of the arm
            fl.sort(key=lambda f: f.calc_center_median().z); nseg = 5; t = len(fl) // nseg
            for j in range(nseg):
                seg = fl[j * t:(j + 1) * t]; k = max(1, len(seg) // 6)
                a = sum((f.calc_center_median() for f in seg[:k]), V()) / k; b = sum((f.calc_center_median() for f in seg[-k:]), V()) / k
                nn = sum((f.normal for f in seg), V()).normalized(); y = (b - a); L = max(y.length, 0.004); y.normalize()
                z = -nn; z = (z - y * z.dot(y)).normalized(); x = y.cross(z)
                from mathutils import Matrix
                lo = mk_light(c, f"PR_Neon{n_blue:02d}", 'AREA', BLUE, 0.02, (a + b) / 2 + nn * 0.0015, shape='RECTANGLE', size=0.003, size_y=L)
                lo.matrix_world = Matrix.Translation((a + b) / 2 + nn * 0.0015) @ Matrix((x, y, z)).transposed().to_4x4()
                lo["emitter"] = on; n_blue += 1
            bm.free(); continue
        isl = islands(bm, fl)
        merged = []          # islands closer than 3 mm = one emitter (ring + core)
        for p, n, A in isl:
            for m in merged:
                if (m[0] - p).length < 0.003: break
            else: merged.append((p, n, A))
        for p, n, A in merged:
            e = 0.035 if on == "Robo_ShoulderEmitter_Glow" else 0.012
            # ON the emitter: 1.5 mm off its surface (was 5 mm -> visibly offset hotspots)
            lo = mk_light(c, f"PR_Neon{n_blue:02d}", 'POINT', BLUE, e, p + n * 0.003, shadow_soft_size=0.003)
            lo["emitter"] = on; n_blue += 1
        bm.free()
    # parent the neon lights to their emitter objects (keep world placement) so they follow the arm
    bpy.context.view_layer.update()
    for lo in c.objects:
        if lo.name.startswith("PR_Neon"):
            par = D.objects[lo["emitter"]]; mw = lo.matrix_world.copy()
            lo.parent = par; lo.matrix_parent_inverse = par.matrix_world.inverted(); lo.matrix_world = mw
    for o in c.objects:
        o.data.use_shadow = True
        o["base_energy"] = o.data.energy
    print("practicals:", len(c.objects), "neon", n_blue, flush=True)

def build_variants():
    for k, vd in VARIANTS.items():
        c = coll(f"HERO_V{k}"); c["variant_name"] = vd["name"]; c["exposure"] = vd["exposure"]; c["look"] = vd["look"]
        c["world"] = vd["world"]; c["prac"] = vd["prac"]; c["glow"] = vd.get("glow", 2.6); c["band_emit"] = vd.get("band_emit", 1.0)
        c["prac_col"] = list(vd.get("prac_col", AMBER)); c["band_es"] = vd.get("band_es", {})
        c["neon"] = vd.get("neon", 1.0); c["neon_soft"] = vd.get("neon_soft", 0.003); c["neon_es"] = vd.get("neon_es", 4.5); c["neon_core"] = vd.get("neon_core", 0.0); c["neon_dist"] = vd.get("neon_dist", 0.0); c["blue_glow"] = vd.get("blue_glow", 0.0)
        c["led"] = list(vd.get("led", []))
        c["emit_glow"] = vd.get("emit_glow", -1.0)
        c["engine"] = vd.get("engine", "EEVEE"); c["cy"] = {k: (list(v) if isinstance(v, tuple) else v) for k, v in vd.get("cy", {}).items() if v is not None}
        sb = vd.get("softbox"); c["sb"] = [sb["az"], sb["el"], sb["r"], sb["strength"], *sb["col"]] if sb else [0, 0, 10, 0, 1, 1, 1]
        for L in vd["lights"]:
            kw = dict(shape=L["shape"], size=L["size"], use_shadow=L.get("shadow", True))
            if L["shape"] == 'RECTANGLE': kw["size_y"] = L["size_y"]
            o = mk_light(c, f"V{k}_{L['n']}", 'AREA', L["col"], L["e"], place_dir(L["tgt"], L["az"], L["el"], L["d"]), **kw)
            aim(o, L["tgt"])
            o.data.diffuse_factor = L.get("diffuse", 1.0); o.data.specular_factor = L.get("specular", 1.0)
            if L.get("diffuse", 1.0) == 0.0: o.data.volume_factor = 0.0
            try: o.data.use_shadow_jitter = bool(L.get("jitter"))
            except Exception: pass
            if vd.get("engine") == "CYCLES" and L.get("specular", 1.0) < 1.0:
                # Cycles ignores light specular_factor: diffuse-only light + glossy-only twin at energy x specular
                o.visible_glossy = False
                t = mk_light(c, f"V{k}_{L['n']}_spec", 'AREA', L["col"], L["e"] * L["specular"], o.location.copy(), **kw)
                t.rotation_euler = o.rotation_euler.copy(); t.visible_diffuse = False; t.visible_transmission = False
                t.visible_volume_scatter = False

def build_cams():
    for k, s in SHOTS.items():
        name = f"CAM_{k}"; o = D.objects.get(name)
        if o is None:
            o = D.objects.new(name, D.cameras.new(name)); sc.collection.objects.link(o)
        cd = o.data; cd.lens = s["lens"]; cd.sensor_fit = s["fit"]; cd.sensor_width = cd.sensor_height = 36
        cd.clip_start = 0.02
        ax, ay = s["aim_xy"]; a = math.radians(s["az"])
        o.location = (ax + s["d"] * math.sin(a), ay - s["d"] * math.cos(a), s["cam_z"])
        o.rotation_euler = (math.pi / 2, 0, a)          # horizontal optical axis, facing the statue
        # lens shift to put frame centre at frame_z (fraction of the larger frame side)
        w, h = s["res"]; vf = 2 * s["d"] * 18 / s["lens"]       # frame size along the fitted side at the subject
        side_h = vf if s["fit"] == 'VERTICAL' else vf * h / w
        big = side_h * max(w, h) / h
        cd.shift_y = (s["frame_z"] - s["cam_z"]) / big; cd.shift_x = 0
        o["res"] = list(s["res"])

def setup_render():
    sc.render.engine = 'BLENDER_EEVEE_NEXT'; ee = sc.eevee
    ee.use_shadows = True; ee.shadow_ray_count = 3; ee.shadow_step_count = 12
    ee.light_threshold = 0.0005
    try:
        ee.use_raytracing = True; ee.ray_tracing_method = 'SCREEN'; ee.ray_tracing_options.resolution_scale = '2'
    except Exception as e: print("rt", e)
    sc.render.film_transparent = True
    sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'
    sc.view_settings.view_transform = 'AgX'
    if "Floor" in D.objects: D.objects["Floor"].hide_render = True; D.objects["Floor"].hide_viewport = True
    for n in ("Key", "Fill", "Rim"):
        if n in D.objects and D.objects[n].type == 'LIGHT': D.objects[n].hide_render = True; D.objects[n].hide_viewport = True
    # world: plain very dark ambient (camera never sees it: film transparent); strength per variant
    w = sc.world; nt = w.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    N = nt.nodes.new; Lk = nt.links.new
    tc = N('ShaderNodeTexCoord'); sd = N('ShaderNodeCombineXYZ'); sd.name = "SoftDir"
    nrm = N('ShaderNodeVectorMath'); nrm.operation = 'NORMALIZE'; Lk(tc.outputs['Generated'], nrm.inputs[0])
    dot = N('ShaderNodeVectorMath'); dot.operation = 'DOT_PRODUCT'; Lk(nrm.outputs[0], dot.inputs[0]); Lk(sd.outputs[0], dot.inputs[1])
    mr = N('ShaderNodeMapRange'); mr.name = "SoftEdge"; mr.interpolation_type = 'SMOOTHSTEP'; Lk(dot.outputs['Value'], mr.inputs['Value'])
    mul = N('ShaderNodeMath'); mul.operation = 'MULTIPLY'; mul.name = "SoftStr"; Lk(mr.outputs[0], mul.inputs[0])
    sc_ = N('ShaderNodeVectorMath'); sc_.operation = 'SCALE'; sc_.name = "SoftCol"; Lk(mul.outputs[0], sc_.inputs['Scale'])
    amb = N('ShaderNodeCombineXYZ'); amb.name = "AmbCol"
    add = N('ShaderNodeVectorMath'); add.operation = 'ADD'; Lk(sc_.outputs[0], add.inputs[0]); Lk(amb.outputs[0], add.inputs[1])
    bg = N('ShaderNodeBackground'); bg.name = "HeroBG"; bg.inputs[1].default_value = 1.0; Lk(add.outputs[0], bg.inputs[0])
    o = N('ShaderNodeOutputWorld'); Lk(bg.outputs[0], o.inputs[0])
    # compositor: beauty RGBA + glow layer (emission pass + headband AOV only, halo only)
    sys.path.insert(0, f"{S}/scripts/c9"); from glowcomp import AOV
    for vl in sc.view_layers:
        vl.use_pass_emit = True
        if AOV not in [a.name for a in vl.aovs]: a = vl.aovs.add(); a.name = AOV; a.type = 'COLOR'
    sc.use_nodes = True; nt = sc.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    rl = nt.nodes.new('CompositorNodeRLayers'); comp = nt.nodes.new('CompositorNodeComposite')
    nt.links.new(rl.outputs['Image'], comp.inputs['Image']); nt.links.new(rl.outputs['Alpha'], comp.inputs['Alpha'])
    g = nt.nodes.new('CompositorNodeGlare'); g.glare_type = 'FOG_GLOW'; g.quality = 'HIGH'; g.threshold = 0.4; g.size = 9; g.mix = 1.0
    nt.links.new(rl.outputs['Emit'], g.inputs['Image'])
    eg = nt.nodes.new('CompositorNodeMixRGB'); eg.name = "HeroEmitGain"; eg.inputs[1].default_value = (0, 0, 0, 1)
    eg.inputs[0].default_value = 1.0; nt.links.new(g.outputs['Image'], eg.inputs[2]); g = eg
    ga = nt.nodes.new('CompositorNodeGlare'); ga.glare_type = 'FOG_GLOW'; ga.quality = 'HIGH'; ga.threshold = 0.0; ga.size = 9; ga.mix = 1.0
    nt.links.new(rl.outputs[AOV], ga.inputs['Image'])
    ma = nt.nodes.new('CompositorNodeMixRGB'); ma.blend_type = 'ADD'; ma.inputs[0].default_value = 2.6; ma.name = "HeroAmberGain"
    nt.links.new(g.outputs['Image'], ma.inputs[1]); nt.links.new(ga.outputs['Image'], ma.inputs[2])
    # neon halo from its own AOV (independent of the headband): AOV "blue_glow" written by the blue glow materials
    for vl in sc.view_layers:
        if "blue_glow" not in [a.name for a in vl.aovs]: a = vl.aovs.add(); a.name = "blue_glow"; a.type = 'COLOR'
    for mn in ("Cyber_GlowBlue", "Cyber_GlowBlueHot"):
        m = D.materials.get(mn)
        if not m: continue
        for x in [x for x in m.node_tree.nodes if x.type == 'OUTPUT_AOV']: m.node_tree.nodes.remove(x)
        ao = m.node_tree.nodes.new('ShaderNodeOutputAOV'); ao.aov_name = "blue_glow"; ao.inputs['Color'].default_value = (*BLUE, 1)
    gb = nt.nodes.new('CompositorNodeGlare'); gb.glare_type = 'FOG_GLOW'; gb.quality = 'HIGH'; gb.threshold = 0.0; gb.size = 8; gb.mix = 1.0
    nt.links.new(rl.outputs["blue_glow"], gb.inputs['Image'])
    mb = nt.nodes.new('CompositorNodeMixRGB'); mb.blend_type = 'ADD'; mb.name = "HeroBlueGain"; mb.inputs[0].default_value = 0.0
    nt.links.new(ma.outputs['Image'], mb.inputs[1]); nt.links.new(gb.outputs['Image'], mb.inputs[2]); ma = mb
    fo = nt.nodes.new('CompositorNodeOutputFile'); fo.name = "HeroGlowOut"; fo.base_path = LAY
    fo.format.file_format = 'PNG'; fo.format.color_mode = 'RGB'
    fo.file_slots[0].path = "glow_tmp_"
    nt.links.new(ma.outputs['Image'], fo.inputs[0])

def clean_marble(sat=0.65):
    """rev5: base colour of 'Marble' through a Hue/Saturation node (veins/rust patches read orange-brown = 'dirty').
    Idempotent; only touches the material in the loaded file (hero_work), never the asset."""
    m = D.materials.get("Marble")
    if not m: return
    nt = m.node_tree; p = [x for x in nt.nodes if x.type == 'BSDF_PRINCIPLED'][0]; hs = nt.nodes.get("HeroMarbleSat")
    if hs is None:
        src = p.inputs['Base Color'].links[0].from_socket
        hs = nt.nodes.new('ShaderNodeHueSaturation'); hs.name = "HeroMarbleSat"
        nt.links.new(src, hs.inputs['Color']); nt.links.new(hs.outputs['Color'], p.inputs['Base Color'])
    hs.inputs['Saturation'].default_value = sat

def set_variant(k):
    for j in VARIANTS:
        lc = bpy.context.view_layer.layer_collection.children.get(f"HERO_V{j}")
        if lc: lc.exclude = (j != k)
    c = D.collections[f"HERO_V{k}"]
    sc.view_settings.exposure = c["exposure"]; sc.view_settings.look = c["look"]
    wn = sc.world.node_tree.nodes; wv = c["world"]
    for i, v in enumerate((0.75, 0.82, 1.0)): wn["AmbCol"].inputs[i].default_value = v * wv
    sb = list(c["sb"]); wn["SoftStr"].inputs[1].default_value = sb[3]
    wn["SoftCol"].inputs[0].default_value = sb[4:7]
    wn["SoftEdge"].inputs['From Min'].default_value = math.cos(math.radians(sb[2]))
    wn["SoftEdge"].inputs['From Max'].default_value = math.cos(math.radians(sb[2] * 0.6))
    set_softdir(0)
    for o in D.collections["HERO_Practicals"].objects:
        o.data.energy = o["base_energy"] * c["prac"]
        if o.name.startswith(("PR_Mod", "PR_Band")): o.data.color = tuple(c.get("prac_col", AMBER))
    n = sc.node_tree.nodes.get("HeroAmberGain")
    if n: n.inputs[0].default_value = c.get("glow", 2.6)
    n = sc.node_tree.nodes.get("HeroEmitGain")
    eg = c.get("emit_glow", -1.0)
    if n: n.inputs[0].default_value = min(1.0, c.get("glow", 2.6)) if eg < 0 else eg
    n = sc.node_tree.nodes.get("HeroBlueGain")
    if n: n.inputs[0].default_value = c.get("blue_glow", 0.0)
    for o in D.collections["HERO_Practicals"].objects:
        if o.name.startswith("PR_Neon"):
            o.data.energy = o["base_energy"] * c.get("neon", 1.0)
            if o.data.type == 'POINT': o.data.shadow_soft_size = c.get("neon_soft", 0.003)
            nd = c.get("neon_dist", 0.0); o.data.use_custom_distance = nd > 0
            if nd > 0: o.data.cutoff_distance = nd
    for mn in ("Cyber_GlowBlue", "Cyber_GlowBlueHot"):
        m = D.materials.get(mn)
        if m:
            p = [x for x in m.node_tree.nodes if x.type == 'BSDF_PRINCIPLED'][0]
            p.inputs['Emission Strength'].default_value = c.get("neon_es", 4.5)
            k = c.get("neon_core", 0.0)       # rev5: whiter emitter core (halo/spill stay #77D9FF)
            p.inputs['Emission Color'].default_value = (*[b * (1 - k) + k for b in BLUE], 1)
    fix_leds(c)
    if c.get("engine", "EEVEE") == "CYCLES" or os.environ.get("ENGINE") == "CYCLES": setup_cycles(c)
    else:
        sc.render.engine = 'BLENDER_EEVEE_NEXT'
        for o in D.collections["HERO_Practicals"].objects:
            if o.name.startswith("PR_Neon"): o.hide_render = False
    for mn in ("Neuro_GlowAmber", "Neuro_GlowRing", "Neuro_Lens"):
        m = D.materials.get(mn)
        if not m: continue
        p = [x for x in m.node_tree.nodes if x.type == 'BSDF_PRINCIPLED'][0]
        if "base_es" not in m: m["base_es"] = p.inputs['Emission Strength'].default_value
        bes = dict(c.get("band_es", {}))
        f = (bes[mn] / m["base_es"]) if mn in bes else c.get("band_emit", 1.0)
        p.inputs['Emission Strength'].default_value = m["base_es"] * f
        for x in m.node_tree.nodes:      # AOV halo scales with it (x band_emit so the halo stays soft)
            if x.type == 'OUTPUT_AOV':
                if "base_aov" not in m: m["base_aov"] = list(x.inputs['Color'].default_value)
                x.inputs['Color'].default_value = [v * c.get("band_emit", 1.0) for v in m["base_aov"][:3]] + [1]
        if c.get("engine", "EEVEE") == "CYCLES":
            cy = c["cy"]; p.inputs['Emission Strength'].default_value *= cy.get("band_es", 1.0)

_LEDS = []
def _led_dots():
    """the 3 forearm indicator dots of Robo_Indicators: (centre, outward normal, half thickness, matched PR_Neon light)"""
    if _LEDS: return _LEDS
    import numpy as np
    o = D.objects["Robo_Indicators"]; bm = ev_mesh(o); dg = bpy.context.evaluated_depsgraph_get()
    gi = [i for i, m in enumerate(o.data.materials) if m and m.name.startswith("Cyber_GlowBlue")]
    fl = [f for f in bm.faces if f.material_index in gi]; fs = set(fl); seen = set()
    prs = [x for x in D.collections["HERO_Practicals"].objects if x.name.startswith("PR_Neon") and x.get("emitter") == "Robo_Indicators"]
    for f in fl:
        if f in seen: continue
        st = [f]; seen.add(f); comp = []
        while st:
            x = st.pop(); comp.append(x)
            for e in x.edges:
                for y in e.link_faces:
                    if y in fs and y not in seen: seen.add(y); st.append(y)
        P = np.array([v.co[:] for g in comp for v in g.verts]); c = P.mean(0)
        w, vec = np.linalg.eigh(np.cov((P - c).T)); ext = np.ptp((P - c) @ vec, axis=0)
        if ext[1] > 0.003: continue                    # elbow ring / wrist lamp: not one of the small dots
        n = V(vec[:, 0]); c = V(c)
        if sc.ray_cast(dg, c + n * 0.004, n)[0]: n = -n   # outward = side where a ray escapes
        lo = min(prs, key=lambda x: (x.matrix_world.translation - c).length)
        _LEDS.append((c, n, float(ext[0]) / 2, lo, [x.index for x in comp]))
    bm.free(); return _LEDS

def fix_leds(c):
    led = list(c.get("led", []))
    dots = _led_dots()
    for cc, n, ht, lo, _ in dots:                 # remember the original placement (other variants unchanged)
        if "led_mw0" not in lo: lo["led_mw0"] = [v for row in lo.matrix_world for v in row]
    sp = D.objects.get("PR_LedSpill")
    if not led:
        from mathutils import Matrix
        for cc, n, ht, lo, _ in dots:
            b = lo["led_mw0"]; lo.matrix_world = Matrix([b[0:4], b[4:8], b[8:12], b[12:16]])
        if sp: sp.hide_render = True
        _led_mat(None); return
    e, reach, soft, off, es, halo, spe, spr = led
    for cc, n, ht, lo, _ in dots:
        lo.matrix_world.translation = cc + n * (ht + off)
        lo.data.energy = e; lo.data.shadow_soft_size = soft
        lo.data.use_custom_distance = True; lo.data.cutoff_distance = reach
    if sp is None:
        sp = mk_light(D.collections["HERO_Practicals"], "PR_LedSpill", 'POINT', BLUE, 0.0, (0, 0, 0), shadow_soft_size=0.006)
        sp["base_energy"] = 0.0; sp.data.use_shadow = True
    m = sum((d[0] for d in dots), V()) / len(dots); nn = sum((d[1] for d in dots), V()).normalized()
    sp.location = m + nn * 0.007; sp.data.energy = spe; sp.data.use_custom_distance = True; sp.data.cutoff_distance = spr
    sp.hide_render = spe <= 0
    _led_mat((es, halo, c.get("neon_core", 0.0)))

def _led_mat(cfg):
    """dots get their own copy of Cyber_GlowBlue (weaker emission + weaker AOV halo); cfg None = shared material back"""
    o = D.objects["Robo_Indicators"]; me = o.data; src = D.materials["Cyber_GlowBlue"]
    m = D.materials.get("Cyber_GlowBlueLED")
    if m is None: m = src.copy(); m.name = "Cyber_GlowBlueLED"
    if m.name not in me.materials: me.materials.append(m)
    si = list(me.materials).index(src); li = list(me.materials).index(m)
    ids = [i for d in _led_dots() for i in d[4]]
    for i in ids: me.polygons[i].material_index = si if cfg is None else li
    if cfg is None: return
    es, halo, k = cfg
    p = [x for x in m.node_tree.nodes if x.type == 'BSDF_PRINCIPLED'][0]
    p.inputs['Emission Strength'].default_value = es
    p.inputs['Emission Color'].default_value = (*[b * (1 - k) + k for b in BLUE], 1)
    for x in m.node_tree.nodes:
        if x.type == 'OUTPUT_AOV': x.inputs['Color'].default_value = (*[b * halo for b in BLUE], 1)

def setup_cycles(c):
    """rev6: Cycles CPU draft. Emissive meshes = the light sources (no fake neon points)."""
    cy = dict(c["cy"]); sc.render.engine = 'CYCLES'; C = sc.cycles
    C.device = 'CPU'; C.samples = int(os.environ.get("SPP", "128")); C.use_adaptive_sampling = True
    C.adaptive_threshold = float(os.environ.get("ADAPT", "0.03")); C.adaptive_min_samples = 16
    C.use_denoising = True; C.denoiser = 'OPENIMAGEDENOISE'; C.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
    C.denoising_prefilter = 'ACCURATE'
    C.max_bounces = 6; C.diffuse_bounces = int(cy.get("gi_d", 2)); C.glossy_bounces = 2; C.transmission_bounces = 2
    C.transparent_max_bounces = 4; C.caustics_reflective = False; C.caustics_refractive = False; C.blur_glossy = 1.0
    C.use_light_tree = True; C.sample_clamp_indirect = 10.0
    try: sc.render.threads_mode = 'AUTO'
    except Exception: pass
    sc.render.film_transparent = True
    for o in D.collections["HERO_Practicals"].objects:
        if o.name.startswith(("PR_Neon", "PR_LedSpill")): o.hide_render = True
        elif o.name.startswith(("PR_Mod", "PR_Band")): o.data.energy = o["base_energy"] * c["prac"] * cy.get("band", 1.0)
    k = cy.get("core", 0.25); col = (*[b * (1 - k) + k for b in BLUE], 1)
    # shoulder emitter: the disc sits nearly flush in the pauldron (surroundings only see it at grazing angles), so its
    # real spill is tiny -> same frosted-film glow around it (sigma ~1.5x the 9 mm disc radius), centre on the disc
    _GLOW_EXTRA.clear()
    sh = D.objects.get("Robo_ShoulderEmitter_Glow")
    if sh is not None and cy.get("sh_glow", 0) > 0:
        bm = ev_mesh(sh); cen = sum((v.co for v in bm.verts), V()) / len(bm.verts); bm.free()
        _GLOW_EXTRA.append((cen, cy.get("sh_sig", 0.014), cy["sh_glow"], cy.get("sh_pw", 2.0)))
    _led_pad(cy.get("pad", (0.55, 0.15, 0.42, 6.0, 0.0022)))
    # rev7 (client): the long accent line on the upper arm is removed (render-hidden here; remove from the asset later)
    ac = D.objects.get("Robo_Glow_AccentUpper")
    if ac is not None: ac.hide_render = bool(cy.get("no_accent", False))
    # rev7: neutral ambient (the bluish AmbCol tinted deep drapery/leg shadows cold)
    if cy.get("ambcol"):
        wv = c["world"]
        for i, v in enumerate(cy["ambcol"]): sc.world.node_tree.nodes["AmbCol"].inputs[i].default_value = v * wv
    if sh is not None and cy.get("sh_rings"): _shoulder_rings(cen, cy["sh_rings"])
    if cy.get("elbow_es"): _elbow_mat(cy["elbow_es"])
    # final: the robot-side blue lights become narrow beams (area-light spread) aimed at the arm/upper torso, so they no
    # longer reach the back drape between the legs (A: KeyBlue gave 5.8% -> 1.3% blue in deep shadows when off)
    for o in [o for o in D.objects if o.type == 'LIGHT' and o.data.type == 'AREA']:
        if "_KeyBlue" in o.name:
            o.data.spread = math.radians(cy.get("blue_spread", 180.0))
        if "_RimBlueR" in o.name:
            o.data.spread = math.radians(cy.get("rim_spread", cy.get("blue_spread", 180.0)))
        # final: KeyBlue light-linked to the robot arm only (it was the source of the cold back-drape strip in A);
        # the marble's robot-side edge keeps its blue from RimBlueR + the arm's own neon
        if "_KeyBlue" in o.name:
            if cy.get("kb_robot_only"):
                rc = D.collections.get("LL_RobotOnly")
                if rc is None:
                    rc = D.collections.new("LL_RobotOnly")
                    for ob in D.objects:
                        if ob.type in ('MESH', 'CURVE') and ob.name.startswith("Robo_"): rc.objects.link(ob)
                o.light_linking.receiver_collection = rc
            else:
                o.light_linking.receiver_collection = None
    # the long accent line (curve Robo_Glow_AccentUpper) is ~10x the area of the other emitters -> own, weaker material
    ac = D.objects.get("Robo_Glow_AccentUpper")
    if ac is not None and ac.data.materials:
        ml = D.materials.get("Cyber_GlowBlueLine")
        if ml is None: ml = D.materials["Cyber_GlowBlue"].copy(); ml.name = "Cyber_GlowBlueLine"
        for i, m in enumerate(ac.data.materials):
            if m and m.name == "Cyber_GlowBlue": ac.data.materials[i] = ml
    for mn, es in (("Cyber_GlowBlue", cy.get("es", 60)), ("Cyber_GlowBlueHot", cy.get("hot", 60)), ("Cyber_GlowBlueLED", cy.get("led_es", 60)),
                   ("Cyber_GlowBlueLine", cy.get("line_es", 60))):
        m = D.materials.get(mn)
        if not m: continue
        p = [x for x in m.node_tree.nodes if x.type == 'BSDF_PRINCIPLED'][0]
        p.inputs['Emission Strength'].default_value = es; p.inputs['Emission Color'].default_value = col
        try: m.cycles.emission_sampling = 'FRONT'
        except Exception: pass
        for x in m.node_tree.nodes:      # halo AOV: keep the EEVEE level (es-independent)
            if x.type == 'OUTPUT_AOV' and mn == "Cyber_GlowBlueLED": x.inputs['Color'].default_value = (*[b * cy.get("led_halo", 0.6) for b in BLUE], 1)
    n = sc.node_tree.nodes.get("HeroEmitGain")
    if n and "emit_glow" in cy: n.inputs[0].default_value = cy["emit_glow"]
    n = sc.node_tree.nodes.get("HeroBlueGain")
    if n and "blue_glow" in cy:
        n.inputs[0].default_value = cy["blue_glow"]        # client: neon halo small + tight (was 2.0-2.6, size 8)
        if n.inputs[2].links: n.inputs[2].links[0].from_node.size = int(cy.get("blue_size", 8))
    n = sc.node_tree.nodes.get("HeroAmberGain")
    if n and "glow" in cy: n.inputs[0].default_value = cy["glow"]
    print("CYCLES", {k: v for k, v in cy.items()}, flush=True)

def _elbow_mat(es):
    """rev7d (client crop: a thin blue light line beside the elbow ring): the ring's grazing light streaked along the
    adjacent plate edge -> the elbow ring + wrist lamp (Cyber_GlowBlue faces of Robo_Indicators that are not LED dots) get
    their own weaker material; the hand disc keeps the shared one."""
    o = D.objects["Robo_Indicators"]; me = o.data
    m = D.materials.get("Cyber_GlowBlueElbow")
    if m is None: m = D.materials["Cyber_GlowBlue"].copy(); m.name = "Cyber_GlowBlueElbow"
    if m.name not in [x.name for x in me.materials if x]: me.materials.append(m)
    names = [x.name if x else "" for x in me.materials]; si = names.index("Cyber_GlowBlue"); ei = names.index(m.name)
    for pl in me.polygons:
        if pl.material_index == si: pl.material_index = ei
    p = [x for x in m.node_tree.nodes if x.type == 'BSDF_PRINCIPLED'][0]
    p.inputs['Emission Strength'].default_value = es; p.inputs['Emission Color'].default_value = (*BLUE, 1)

def _shoulder_rings(cen, cfg):
    """rev7: shoulder disc = readable lens structure instead of a flat white blob: emission strength by radius from the
    disc centre (constant ColorRamp: core / dark gap / bright ring / dark gap / outer ring), the bezel ring (Robo_Mechanics
    glow faces) gets its own weaker copy. cfg = (core, ring, gap, bezel_es, R)."""
    core, ring, gap, bez, R = cfg
    m = D.materials["Cyber_GlowBlueHot"]; nt = m.node_tree; b = [x for x in nt.nodes if x.type == 'BSDF_PRINCIPLED'][0]
    for x in [x for x in nt.nodes if x.name.startswith("SHR")]: nt.nodes.remove(x)
    N = nt.nodes.new; Lk = nt.links.new
    g = N('ShaderNodeNewGeometry'); g.name = "SHR_geo"
    dv = N('ShaderNodeVectorMath'); dv.name = "SHR_d"; dv.operation = 'DISTANCE'; Lk(g.outputs['Position'], dv.inputs[0]); dv.inputs[1].default_value = cen[:]
    q = N('ShaderNodeMath'); q.name = "SHR_q"; q.operation = 'DIVIDE'; Lk(dv.outputs['Value'], q.inputs[0]); q.inputs[1].default_value = R
    cr = N('ShaderNodeValToRGB'); cr.name = "SHR_ramp"; cr.color_ramp.interpolation = 'EASE'; Lk(q.outputs[0], cr.inputs[0])
    el = cr.color_ramp.elements
    stops = [(0.0, core), (0.28, core), (0.38, gap), (0.55, ring), (0.68, ring), (0.78, gap), (0.9, ring * 0.6), (1.0, gap)]
    while len(el) > 2: el.remove(el[-1])
    el[0].position, el[0].color = stops[0][0], (stops[0][1],) * 3 + (1,)
    el[1].position, el[1].color = stops[1][0], (stops[1][1],) * 3 + (1,)
    for pos, v in stops[2:]:
        e = el.new(pos); e.color = (v, v, v, 1)
    mx = N('ShaderNodeMath'); mx.name = "SHR_scale"; mx.operation = 'MULTIPLY'; Lk(cr.outputs['Color'], mx.inputs[0]); mx.inputs[1].default_value = 1.0
    Lk(mx.outputs[0], b.inputs['Emission Strength'])
    # bezel ring of the shoulder emitter (Robo_Mechanics glow faces) -> own material, weaker
    o = D.objects["Robo_Mechanics"]; me = o.data
    mb = D.materials.get("Cyber_GlowBlueBezel")
    if mb is None: mb = D.materials["Cyber_GlowBlue"].copy(); mb.name = "Cyber_GlowBlueBezel"
    if mb.name not in [x.name for x in me.materials if x]: me.materials.append(mb)
    names = [x.name if x else "" for x in me.materials]; bi = names.index(mb.name)
    for i, x in enumerate(names):
        if x == "Cyber_GlowBlue":
            for pl in me.polygons:
                if pl.material_index == i: pl.material_index = bi
    pb = [x for x in mb.node_tree.nodes if x.type == 'BSDF_PRINCIPLED'][0]
    pb.inputs['Emission Strength'].default_value = bez; pb.inputs['Emission Color'].default_value = (*BLUE, 1)

def _led_pad(cfg):
    """rev6 Cycles: the small housing pad that carries the 3 forearm LEDs (AI_Titanium_Joint faces of Robo_Indicators
    within 12 mm of the dots) gets a satin, mostly dielectric finish (base, metallic, roughness). On the 85% metal the
    near-field LED light only shows as a mirror lobe somewhere else; on satin each LED lights its own small pool."""
    o = D.objects["Robo_Indicators"]; me = o.data; mats = list(me.materials)
    src = D.materials["AI_Titanium_Joint"]; m = D.materials.get("Cyber_LEDPad")
    if m is None: m = src.copy(); m.name = "Cyber_LEDPad"
    if m.name not in [x.name for x in me.materials if x]: me.materials.append(m)
    mats = [x.name if x else "" for x in me.materials]; si = mats.index(src.name); pi = mats.index(m.name)
    cen = sum((d[0] for d in _led_dots()), V()) / 3; Mi = o.matrix_world.inverted(); cl = Mi @ cen
    sca = o.matrix_world.to_scale()[0]
    for p in me.polygons:
        if p.material_index in (si, pi) and (p.center - cl).length * sca < 0.012: p.material_index = pi
    b = [x for x in m.node_tree.nodes if x.type == 'BSDF_PRINCIPLED'][0]
    b.inputs['Base Color'].default_value = (cfg[0], cfg[0] * 1.02, cfg[0] * 1.06, 1)
    b.inputs['Metallic'].default_value = cfg[1]; b.inputs['Roughness'].default_value = cfg[2]
    A, sig = (cfg[3], cfg[4]) if len(cfg) > 4 else (0.0, 0.002)
    pw = cfg[5] if len(cfg) > 5 else 2.0
    spots = [(d[0], sig, A, pw) for d in _led_dots()] + list(_GLOW_EXTRA)
    for mn in ("Cyber_LEDPad", "AI_Titanium", "AI_Titanium_Joint"):
        _led_glow(D.materials[mn], spots)
        # big shared plate materials: no light-tree emitter sampling (it blacked the plates out); the pad is sampled
        D.materials[mn].cycles.emission_sampling = 'FRONT' if mn == "Cyber_LEDPad" else 'NONE'

_GLOW_EXTRA = []      # extra (centre, sigma, amp) film-glow spots (set by setup_cycles: shoulder emitter)
def _led_glow(m, spots):
    """rev6 Cycles: the LEDs sit in a thin frosted light-guide film on the plate: emission = A * sum_i exp(-(d_i/sigma)^2)
    around each dot centre (world space) -> 3 equal, overlapping pools, brightest at each LED, following the plate
    surface; ~0 farther than 3 sigma. Emissive, so in Cycles it also lights its surroundings."""
    b = [x for x in m.node_tree.nodes if x.type == 'BSDF_PRINCIPLED'][0]
    nt = m.node_tree
    for x in [x for x in nt.nodes if x.name.startswith("LEDG")]: nt.nodes.remove(x)
    N = nt.nodes.new; Lk = nt.links.new
    geo = N('ShaderNodeNewGeometry'); geo.name = "LEDG_geo"; acc = None
    for i, (cen, sig, A, pw) in enumerate(spots):
        dv = N('ShaderNodeVectorMath'); dv.name = f"LEDG_d{i}"; dv.operation = 'DISTANCE'
        Lk(geo.outputs['Position'], dv.inputs[0]); dv.inputs[1].default_value = cen[:]
        q = N('ShaderNodeMath'); q.name = f"LEDG_q{i}"; q.operation = 'DIVIDE'; Lk(dv.outputs['Value'], q.inputs[0]); q.inputs[1].default_value = sig
        # exponent pw > 2 = super-gaussian: flatter pool with a defined edge (client: crisper, not fog)
        q2 = N('ShaderNodeMath'); q2.name = f"LEDG_s{i}"; q2.operation = 'POWER'; Lk(q.outputs[0], q2.inputs[0]); q2.inputs[1].default_value = pw
        ng = N('ShaderNodeMath'); ng.name = f"LEDG_n{i}"; ng.operation = 'MULTIPLY'; Lk(q2.outputs[0], ng.inputs[0]); ng.inputs[1].default_value = -1
        ex0 = N('ShaderNodeMath'); ex0.name = f"LEDG_x{i}"; ex0.operation = 'EXPONENT'; Lk(ng.outputs[0], ex0.inputs[0])
        ex = N('ShaderNodeMath'); ex.name = f"LEDG_e{i}"; ex.operation = 'MULTIPLY'; Lk(ex0.outputs[0], ex.inputs[0]); ex.inputs[1].default_value = A
        if acc is None: acc = ex
        else:
            ad = N('ShaderNodeMath'); ad.name = f"LEDG_a{i}"; ad.operation = 'ADD'; Lk(acc.outputs[0], ad.inputs[0]); Lk(ex.outputs[0], ad.inputs[1]); acc = ad
    am = N('ShaderNodeMath'); am.name = "LEDG_amp"; am.operation = 'MULTIPLY'; Lk(acc.outputs[0], am.inputs[0]); am.inputs[1].default_value = 1.0
    Lk(am.outputs[0], b.inputs['Emission Strength']); b.inputs['Emission Color'].default_value = (*BLUE, 1)

def set_softdir(deg):
    c = [x for x in D.collections if x.name.startswith("HERO_V") and not bpy.context.view_layer.layer_collection.children[x.name].exclude]
    if not c: return
    sb = c[0]["sb"]; d = place_dir((0, 0, 0), sb[0] + deg, sb[1], 1.0)
    for i in range(3): sc.world.node_tree.nodes["SoftDir"].inputs[i].default_value = d[i]

def store_base():
    """remember the un-rotated placement of cameras + variant rigs (for set_rot)"""
    for k in VARIANTS:     # excluded collections are not evaluated -> matrix_world would be identity
        lc = bpy.context.view_layer.layer_collection.children.get(f"HERO_V{k}")
        if lc: lc.exclude = False
    bpy.context.view_layer.update()
    for o in [D.objects[f"CAM_{k}"] for k in SHOTS] + [o for k in VARIANTS for o in D.collections[f"HERO_V{k}"].objects]:
        o["base_mw"] = [v for row in o.matrix_world for v in row]

def set_rot(deg, lights=True):
    """orbit camera + light rig about the statue's vertical axis (through x=y=0). +deg = counter-clockwise seen from
    above = camera moves towards the statue's LEFT (+X) = HUMAN arm side; -deg = towards the ROBOT arm."""
    from mathutils import Matrix
    R = Matrix.Rotation(math.radians(deg), 4, 'Z')
    for o in [D.objects[f"CAM_{k}"] for k in SHOTS] + [o for k in VARIANTS for o in D.collections[f"HERO_V{k}"].objects]:
        lr = Matrix.Rotation(math.radians(float(os.environ["LIGHT_ROT"])), 4, 'Z') if os.environ.get("LIGHT_ROT") else (R if lights else Matrix.Identity(4))
        rr = R if o.type == 'CAMERA' else lr
        b = o["base_mw"]; o.matrix_world = rr @ Matrix([b[0:4], b[4:8], b[8:12], b[12:16]])
    set_softdir(float(os.environ["LIGHT_ROT"]) if os.environ.get("LIGHT_ROT") else (deg if lights else 0))

def set_shot(k, scale=1.0):
    cam = D.objects[f"CAM_{k}"]; sc.camera = cam
    sc.render.resolution_x, sc.render.resolution_y = [int(round(v * scale)) for v in cam["res"]]
    sc.render.resolution_percentage = 100
    bd = os.environ.get("BORDER")       # quick look: "xmin,ymin,xmax,ymax" (fractions, y from bottom)
    sc.render.use_border = bool(bd); sc.render.use_crop_to_border = False
    if bd:
        sc.render.border_min_x, sc.render.border_min_y, sc.render.border_max_x, sc.render.border_max_y = [float(v) for v in bd.split(",")]

PROBES = {   # rough 3D guesses; a ray from the camera through each finds the real surface hit
 "band_module": (0.024, -0.042, 0.947), "band_strip": (0.030, -0.020, 0.946), "band_strip2": (-0.004, -0.058, 0.945),
 "hair_above": (0.018, -0.036, 0.966), "hair_above2": (-0.004, -0.052, 0.965), "forehead": (0.024, -0.050, 0.925),
 "forehead2": (0.005, -0.062, 0.924), "hair_side": (0.038, 0.000, 0.930),
}
def probe(stem):
    import json
    from bpy_extras.object_utils import world_to_camera_view
    dg = bpy.context.evaluated_depsgraph_get(); cam = sc.camera; o = cam.matrix_world.translation
    W, H = sc.render.resolution_x, sc.render.resolution_y; res = {}
    for k, p in PROBES.items():
        p = V(p); hit, loc, n, i, ob, m = sc.ray_cast(dg, o, (p - o).normalized())
        q = loc if hit else p; c = world_to_camera_view(sc, cam, q)
        res[k] = dict(px=round(c.x * W), py=round((1 - c.y) * H), obj=ob.name if hit else None)
    # face box: projected bbox of the marble verts of the face (z .835-.928, in front of the head along its gaze)
    import numpy as np
    ob = D.objects["Sculpture_HiRes"]; me = ob.data; co = np.empty(len(me.vertices) * 3, np.float32)
    me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    M = np.array(ob.matrix_world); co = co @ M[:3, :3].T + M[:3, 3]
    g = np.array([0.81, -0.58]); rel = co[:, :2] - np.array([-0.030, -0.003])
    sel = co[(co[:, 2] > 0.835) & (co[:, 2] < 0.928) & (rel @ g > 0.045)]
    if len(sel) > 20000: sel = sel[np.linspace(0, len(sel) - 1, 20000).astype(int)]
    px = [world_to_camera_view(sc, cam, V(tuple(float(x) for x in q))) for q in sel]
    xs = [c.x * W for c in px]; ys = [(1 - c.y) * H for c in px]
    res["face_tl"] = dict(px=int(min(xs)), py=int(min(ys)), obj=None); res["face_br"] = dict(px=int(max(xs)), py=int(max(ys)), obj=None)
    json.dump(res, open(f"{LAY}/{stem}_probe.json", "w"), indent=1)

def render(k, shot, scale, spp, tag="", rot=None):
    if rot is not None: tag = f"_r{rot:+03d}{tag}"
    b = f"{LAY}/{shot}_v{k}{tag}_beauty.png"; gl = f"{LAY}/{shot}_v{k}{tag}_glow.png"
    if os.path.exists(b) and os.path.exists(gl) and os.environ.get("FORCE") != "1": print("SKIP", b, flush=True); return
    set_variant(k); set_shot(shot, scale); sc.eevee.taa_render_samples = spp
    if sc.render.engine == 'CYCLES': sc.cycles.samples = spp
    set_rot(rot or 0, lights=os.environ.get("LIGHTS_FIXED") != "1")
    cam = sc.camera; sh = SHOTS[shot]; dz = 0.0
    if os.environ.get("CAMZ"):      # raise/lower the camera, keep the frame (horizontal axis + lens shift)
        w, h = sh["res"]; vf = 2 * sh["d"] * 18 / sh["lens"]; side_h = vf if sh["fit"] == 'VERTICAL' else vf * h / w
        big = side_h * max(w, h) / h; dz = float(os.environ["CAMZ"]) - sh["cam_z"]
        cam.location.z = sh["cam_z"] + dz; cam.data.shift_y = (sh["frame_z"] - cam.location.z) / big
    else:
        w, h = sh["res"]; vf = 2 * sh["d"] * 18 / sh["lens"]; side_h = vf if sh["fit"] == 'VERTICAL' else vf * h / w
        cam.data.shift_y = (sh["frame_z"] - sh["cam_z"]) / (side_h * max(w, h) / h)
    sc.render.filepath = b + ".tmp.png"; import time; t0 = time.time(); bpy.ops.render.render(write_still=True)
    print("RENDER_TIME", shot, k, f"{time.time() - t0:.0f}s", sc.render.engine, sc.render.resolution_x, sc.render.resolution_y, flush=True)
    os.replace(b + ".tmp.png", b)
    tmp = [f for f in os.listdir(LAY) if f.startswith("glow_tmp_")]
    os.replace(f"{LAY}/{sorted(tmp)[-1]}", gl)
    probe(os.path.basename(b)[:-len("_beauty.png")])
    print("RENDERED", shot, k, flush=True)

def refresh_rigs():
    """hero_work.blend only: rebuild the variant rigs from VARIANTS and move the PR_ModDn spill lights (no asset)"""
    for o in list(D.objects):
        if o.name.startswith("V") and o.type == 'LIGHT' and "_" in o.name: pass
    build_variants()
    HC = V((-0.030, -0.003, 0.0))
    for o in D.collections["HERO_Practicals"].objects:
        if o.name.startswith("PR_ModDn"):
            i = o.name[len("PR_ModDn"):]; m = D.objects[f"PR_Mod{i}"].location
            r = V((m.x - HC.x, m.y - HC.y, 0)).normalized(); p = m - r * 0.007
            o.location = p + r * 0.030 + V((0, 0, -0.008)); o.data.shadow_soft_size = 0.012; o["base_energy"] = 0.0025
        if o.name.startswith("PR_Mod") and o.name[6:].isdigit(): o["base_energy"] = 0.020
        if o.name.startswith("PR_ModUp"):
            i = o.name[len("PR_ModUp"):]; m = D.objects[f"PR_Mod{i}"].location
            r = V((m.x - HC.x, m.y - HC.y, 0)).normalized(); p = m - r * 0.007
            o.location = p + r * 0.020 + V((0, 0, 0.014)); o.data.shadow_soft_size = 0.008; o["base_energy"] = 0.005
    from brand_recolor import recolor; recolor(verbose=False)
    store_base(); set_variant(2)

if __name__ == "__main__":
    if os.path.basename(bpy.data.filepath) != "hero_work.blend":
        from brand_recolor import recolor; recolor()   # brand colours on the work copy
    fresh = os.path.basename(bpy.data.filepath) != "hero_work.blend"   # run on hero_work.blend = render only
    if not fresh and os.environ.get("REFRESH") == "1":
        refresh_rigs(); bpy.ops.wm.save_mainfile(); print("refreshed rigs in hero_work.blend", flush=True)
    if fresh:
        build_practicals(); build_variants(); build_cams(); setup_render(); store_base()
        set_variant(1); set_shot("A")
    if fresh and os.environ.get("NOSAVE") != "1":
        bpy.ops.wm.save_as_mainfile(filepath=f"{OUT}/hero_work.blend", copy=True)
        # keep this script inside the .blend as a text block for switching variants
        print("saved hero_work.blend", flush=True)
    if "render" in argv:
        vs = [int(x) for x in os.environ.get("VARIANT", "1,2,3").split(",")]
        shots = os.environ.get("SHOTS", "A,B").split(",")
        rots = [int(x) for x in os.environ["ROT"].split(",")] if os.environ.get("ROT") else [None]
        for k in vs:
            for r in rots:
                for s in shots: render(k, s, float(os.environ.get("SCALE", "1")), int(os.environ.get("SPP", "16")), os.environ.get("TAG", ""), r)
