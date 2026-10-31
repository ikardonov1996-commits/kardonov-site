# hero_work.blend + hero variant 42 (approved hero final setup: brand recolour, accent hidden, LED/elbow/shoulder mats,
# satin LED pad, headband emission + PR_Mod/PR_Band practicals, neon point lights off) -> out/stage6/cyber_prep.blend
import bpy, sys, os
S = "/tmp/claude-0/-home-user-kardonov-site/cb30cd45-1b88-5b9b-b3ff-480343f6cfce/scratchpad"
sys.path.insert(0, S + "/scripts/hero"); import hero_light as H
sc = bpy.context.scene
H.build_variants(); H.build_cams(); H.store_base(); H.clean_marble(0.45)
H.set_variant(42); H.set_shot("A", 1.0); H.set_rot(0)
D = bpy.data
for o in D.collections["HERO_Practicals"].objects:
    print("PR", o.name, round(o.data.energy, 5), o.hide_render, tuple(round(x, 3) for x in o.matrix_world.translation))
for m in D.materials:
    if m.name.startswith(("Cyber_", "Neuro_")):
        p = [x for x in m.node_tree.nodes if x.type == 'BSDF_PRINCIPLED']
        if p: print("MAT", m.name, p[0].inputs['Emission Strength'].default_value, p[0].inputs['Emission Strength'].is_linked, tuple(round(x, 3) for x in p[0].inputs['Emission Color'].default_value))
print("accent hide_render", D.objects["Robo_Glow_AccentUpper"].hide_render)
print("Sculpture parent", D.objects["Sculpture_HiRes"].parent, tuple(D.objects["Sculpture_HiRes"].matrix_world.translation))
bpy.ops.wm.save_as_mainfile(filepath=S + "/out/stage6/cyber_prep.blend", copy=True); print("SAVED_PREP")
