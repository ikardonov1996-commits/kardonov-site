# Brand recolour of the emissive parts of the cyber-David (by MATERIAL NAME, idempotent).
#   blue neon / indicators  (#3fa9ff)          -> #77D9FF  (AI blue)
#   headband glow/rings/lens (amber 1,.36,.04)  -> #FCCB84  (champagne)
# Neuro_Gold (band metal) -> pale champagne gold (rev3, see METALS). Emission strengths are kept; AOV "amber_glow" colours keep their intensity
# (max channel) but take the new hue.
# Use:  blender -b FILE.blend -P brand_recolor.py                 (recolours in memory only, nothing saved)
#       blender -b FILE.blend -P brand_recolor.py -- --save       (recolour + save FILE.blend in place)
#       blender -b FILE.blend -P brand_recolor.py -- --out X.blend (recolour + save a copy)
#   or from another script:  sys.path.insert(0, ".../scripts"); from brand_recolor import recolor; recolor()
import bpy, sys

def lin(h):
    h = h.lstrip("#"); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)
BLUE_SRGB_LIN = lin("77D9FF")     # (0.184, 0.693, 1.000)  plain sRGB->linear (reference only)
CHAMP_SRGB_LIN = lin("FCCB84")    # (0.973, 0.597, 0.231)
# AgX compensation (OCIO inverse fit, scripts/tl6/agx_fit.py): plain sRGB->linear values come out washed/grey through
# AgX (#77D9FF -> ~#91B8C6, #FCCB84 -> ~#C7AE8E). These linear colours give the closest reachable on-screen hues
# (AgX + "Medium High Contrast" look, strength ~2-3: blue ~#A5D2F0, champagne ~#F3CD97). Use them for emission AND
# for coloured lights. Exact brand RGB for the glow layer is restored in post (alpha = intensity).
BLUE = (0.0, 0.443, 1.0)
CHAMP = (1.0, 0.487, 0.0)
# headband emission (rev3): inverse fit with the hero's AgX "Medium High Contrast" look (scripts/hero/agx_inv_look.py):
# (1, .472, .028) x ~2.6 displays #F0C894 (exact #FCCB84 is out of AgX gamut). (1,.487,0) at low strength reads lemon.
HEAD_EMIT = (1.0, 0.476, 0.09)    # rev4: fit for #DCAE78 (peach-champagne at strength ~1.4); rev3 was (1,.472,.028)

# material name -> (target colour, base-colour factor)   base = colour * factor (keeps the old darkness of the base)
MATERIALS = {
    "Cyber_GlowBlue":    (BLUE, 1.0),
    "Cyber_GlowBlueHot": (BLUE, 1.0),
    "Neuro_GlowAmber":   (HEAD_EMIT, 0.05),
    "Neuro_GlowRing":    (HEAD_EMIT, 0.05),
    "Neuro_Lens":        (HEAD_EMIT, 0.30),
}

# rev3 (client): headband metal from yellow gold (1,.58,.2) to a pale champagne gold (target on screen ~#E8C79A)
METALS = {"Neuro_Gold": dict(base=(0.80, 0.62, 0.42), rough=0.45)}

def recolor(scene=None, verbose=True):
    done = []
    for name, d in METALS.items():
        m = bpy.data.materials.get(name)
        if not m or not m.node_tree: continue
        for n in m.node_tree.nodes:
            if n.type == 'BSDF_PRINCIPLED':
                n.inputs['Base Color'].default_value = (*d["base"], 1); n.inputs['Roughness'].default_value = d["rough"]
        m.diffuse_color = (*d["base"], 1); done.append(name)
    for name, (col, bf) in MATERIALS.items():
        m = bpy.data.materials.get(name)
        if not m or not m.node_tree:
            if verbose: print("brand_recolor: missing", name); continue
        for n in m.node_tree.nodes:
            if n.type == 'BSDF_PRINCIPLED':
                n.inputs['Emission Color'].default_value = (*col, 1)
                if not n.inputs['Base Color'].is_linked:
                    n.inputs['Base Color'].default_value = (col[0] * bf, col[1] * bf, col[2] * bf, 1)
            elif n.type == 'EMISSION':
                n.inputs['Color'].default_value = (*col, 1)
            elif n.type == 'OUTPUT_AOV':
                old = n.inputs['Color'].default_value; k = max(old[0], old[1], old[2]) / max(col)
                n.inputs['Color'].default_value = (col[0] * k, col[1] * k, col[2] * k, 1)
        m.diffuse_color = (*col, 1)
        done.append(name)
    if verbose: print("brand_recolor: recoloured", done, flush=True)
    return done

if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    recolor()
    if "--save" in argv:
        bpy.ops.wm.save_mainfile(); print("brand_recolor: saved", bpy.data.filepath)
    elif "--out" in argv:
        p = argv[argv.index("--out") + 1]; bpy.ops.wm.save_as_mainfile(filepath=p, copy=True); print("brand_recolor: saved copy", p)
    else:
        print("brand_recolor: dry run (nothing saved); pass -- --save or -- --out FILE")
