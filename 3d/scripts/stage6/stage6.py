# KARDONOV carving stage 6 = finished CYBER David, same scene/camera/light rig v3b as stages 1-5.
#   build : blender -b out/stages_light/stages_work.blend -P scripts/stage6/stage6.py -- build6
#           Sculpture_HiRes keeps its object/transform/animation/material (Marble_Carve) but gets the cyber asset's marble
#           mesh (same lineage, right arm removed); robot arm + headband appended from out/stage6/cyber_prep.blend
#           (= hero_work + hero variant 42 = approved hero final look). Headband PR_Mod/PR_Band practicals as in the hero
#           Cycles final; neon = emissive meshes only. Saved to out/stage6/stage6_work.blend.
#   render: blender -b out/stage6/stage6_work.blend -P scripts/stage6/stage6.py -- render6 OUTDIR W H SPP   (env NSTRIP, ADAPT, BUDGET)
#   glow  : ... -- glow6 OUTDIR W H     (16 spp, compositor fog-glow of the AOVs as in hero_final_run.py MODE=glow)
import bpy, sys, os, time, math
S = "/tmp/claude-0/-home-user-kardonov-site/cb30cd45-1b88-5b9b-b3ff-480343f6cfce/scratchpad"
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
sys.path.insert(0, S + "/scripts/stages_light"); import stages_light as SL      # argv[0] != SL commands -> import only
D = bpy.data; sc = bpy.context.scene; O = D.objects
PREP = S + "/out/stage6/cyber_prep.blend"; WORK6 = S + "/out/stage6/stage6_work.blend"
EXTRA = os.environ.get("EXTRA", "")

def build6():
    st = O["Sculpture_HiRes"]
    with D.libraries.load(PREP, link=False) as (src, dst):
        names = [n for n in src.objects if n.startswith(("Robo_", "Neuro_", "PR_Mod", "PR_Band"))]
        dst.objects = names; dst.meshes = ["Sculpture_HiRes"] if "Sculpture_HiRes" in src.meshes else []
    c = D.collections.new("CYBER6"); sc.collection.children.link(c)
    cyber_mesh = None
    for m in dst.meshes: cyber_mesh = m
    if cyber_mesh is None:            # mesh named differently: take it from the appended parent object
        cyber_mesh = dst.objects[0].parent.data
    for o in dst.objects:
        if o is None: continue
        c.objects.link(o)
        if o.parent is not None:      # appended cyber Sculpture_HiRes (identity) -> stage Sculpture_HiRes (identity)
            mw = o.matrix_world.copy(); o.parent = st; o.matrix_parent_inverse.identity(); o.matrix_world = mw
    for o in list(D.objects):
        if o.name.startswith("Sculpture_HiRes.") and o.users_collection == (): D.objects.remove(o)
    # --- marble: same object, cyber mesh, stage marble material
    import numpy as np
    from mathutils import kdtree
    old = st.data; cyber_mesh.name = "Sculpture_Cyber_Mesh"
    co_o = np.empty(len(old.vertices) * 3, np.float32); old.vertices.foreach_get("co", co_o); co_o = co_o.reshape(-1, 3)
    co_c = np.empty(len(cyber_mesh.vertices) * 3, np.float32); cyber_mesh.vertices.foreach_get("co", co_c); co_c = co_c.reshape(-1, 3)
    kd = kdtree.KDTree(len(co_o))
    for i, p in enumerate(co_o): kd.insert(p, i)
    kd.balance(); idx = np.linspace(0, len(co_c) - 1, 40000).astype(int)
    d = np.array([kd.find(co_c[i])[2] for i in idx])
    print("GEO cyber->stage nearest dist: median %.2e  p99 %.2e  max %.2e  >0.1mm %.3f%%" % (np.median(d), np.percentile(d, 99), d.max(), 100 * (d > 1e-4).mean()), flush=True)
    cyber_mesh.materials.clear(); cyber_mesh.materials.append(old.materials[0])
    st.data = cyber_mesh
    # Marble_Carve uses Generated coords -> keep the stage mesh's texture space (cyber mesh bbox is narrower: arm removed)
    cyber_mesh.use_auto_texspace = False
    cyber_mesh.texspace_location = old.texspace_location[:]; cyber_mesh.texspace_size = old.texspace_size[:]
    print("TEXSPACE", tuple(old.texspace_location), tuple(old.texspace_size), flush=True)
    # light linking: the cyber parts receive the same figure-only fills (FaceFill/AbsFill/HeadFill) as the marble
    rc = D.collections.get("SL_LINK_FIG")
    if rc is None:
        rc = D.collections.new("SL_LINK_FIG")
        for n in SL.FIG: rc.objects.link(O[n])
    for o in c.objects:
        if o.type in ('MESH', 'CURVE') and o.name not in rc.objects: rc.objects.link(o)
    print("use_nodes", sc.use_nodes, "aovs", [a.name for a in sc.view_layers[0].aovs], "lights", sum(o.type == 'LIGHT' for o in c.objects),
          "objs", len(c.objects), flush=True)
    bpy.ops.wm.save_as_mainfile(filepath=WORK6, copy=True); print("SAVED", WORK6, flush=True)

ARMKEY = float(os.environ.get("ARMKEY", "0.25"))       # key on the titanium = KeyWarm x ARMKEY, cool-neutral (hero kbcol)
ARMCOL = tuple(float(x) for x in os.environ.get("ARMCOL", "0.86/0.9/1.0").split("/"))
ARMEXCL = os.environ.get("ARMEXCL", "SL_KeyWarm,SL_KeyWarm_spec,SL_Skylight,SL_Skylight_spec,SL_SideFill,SL_SideFill_spec").split(",")
def arm_light():
    """stage 6: in the stage rig the champagne key comes from the ROBOT side (az -48) and front-lit the titanium beige
    (hero: arm lit from behind/the far side -> dark gunmetal + its own neon + rims). The robot parts (Robo_*) are excluded
    from the broad key/top/side lights and the figure-only fills and get a cool-neutral copy of the key at ARMKEY x energy
    (= hero 'KeyBlue' neutral cool-white side key idea). Marble + headband keep the v3b rig unchanged; rims and bounce
    hit everything."""
    robo = [o for o in D.collections["CYBER6"].objects if o.type in ('MESH', 'CURVE') and o.name.startswith("Robo_")]
    fig = D.collections.get("SL_LINK_FIG")
    if fig:
        for o in robo:
            if o.name in fig.objects: fig.objects.unlink(o)
    ex = D.collections.get("SL6_EXCL_ROBO") or D.collections.new("SL6_EXCL_ROBO")
    inc = D.collections.get("SL6_ONLY_ROBO") or D.collections.new("SL6_ONLY_ROBO")
    for o in robo:
        if o.name not in ex.objects: ex.objects.link(o)
        if o.name not in inc.objects: inc.objects.link(o)
    L = D.collections["STAGE_LIGHT"]
    for n in ARMEXCL:
        lo = O.get(n)
        if lo is None: continue
        lo.light_linking.receiver_collection = ex
        for cl in ex.collection_objects: cl.light_linking.link_state = 'EXCLUDE'
    for n in ("SL_KeyWarm", "SL_KeyWarm_spec"):
        src = O[n]; t = src.copy(); t.data = src.data.copy(); t.name = n.replace("SL_KeyWarm", "SL6_ArmKey"); L.objects.link(t)
        t.data.energy = src.data.energy * ARMKEY; t.data.color = ARMCOL; t.light_linking.receiver_collection = inc
        for cl in inc.collection_objects: cl.light_linking.link_state = 'INCLUDE'
    print("ARMLIGHT robo", len(robo), "ARMKEY", ARMKEY, ARMCOL, flush=True)

def prep(w, h, spp):
    SL.build_light(); SL.setup_cycles(spp)
    if ARMKEY >= 0: arm_light()
    if EXTRA:      # e.g. EXTRA="es=180,band=1.0"  quick tweak hooks
        for kv in EXTRA.split(","):
            k, v = kv.split("="); v = float(v)
            if k == "es":
                for mn in ("Cyber_GlowBlue",): D.materials[mn].node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = v
            if k == "band":
                for o in D.collections["CYBER6"].objects:
                    if o.type == 'LIGHT': o.data.energy *= v
    r = sc.render; r.resolution_x = w; r.resolution_y = h; r.resolution_percentage = 100
    sc.frame_set(list(sc["stage_frames"])[SL.ALL.index("Sculpture_HiRes")])
    for m in SL.ALL: O[m].hide_render = (m != "Sculpture_HiRes")
    return r

def render6(out, w, h, spp):
    os.makedirs(f"{out}/parts", exist_ok=True); fn = f"{out}/stage_6.png"
    if os.path.exists(fn): print("STILL exists", fn, flush=True); return
    r = prep(w, h, spp); r.use_border = True; r.use_crop_to_border = False; N = SL.NSTRIP; last = 0.0
    for k in range(N):
        pf = f"{out}/parts/stage_6_s{k}.png"
        if os.path.exists(pf): continue
        est = float(os.environ.get("STRIP_EST", "0")) or last
        if est and time.time() - SL.T0 + 1.15 * est > SL.BUDGET:
            print("STRIP budget: stop before", 6, k, "(next run continues)", flush=True); return
        t1 = time.time(); y0, y1 = k * h // N, (k + 1) * h // N
        r.border_min_x, r.border_max_x = 0.0, 1.0
        r.border_min_y = max(0, y0 - SL.PAD) / h; r.border_max_y = min(h, y1 + SL.PAD) / h
        tmp = f"{out}/parts/stage_6_s{k}.part.png"; r.filepath = tmp
        bpy.ops.render.render(write_still=True); os.replace(tmp, pf)
        last = time.time() - t1; print("STRIP", 6, k, "%.0fs" % last, flush=True)
    SL.assemble(out, 6, w, h); print("STILL", 6, fn, flush=True)

def glow6(out, w, h):
    if os.path.exists(f"{out}/stage_6_glowraw_champ.png"): print("SKIP glow", flush=True); return
    r = prep(w, h, 16); r.use_border = False; sc.cycles.use_denoising = False; sc.cycles.use_adaptive_sampling = False
    vl = sc.view_layers[0]
    for an in ("amber_glow", "blue_glow"):
        if an not in [a.name for a in vl.aovs]: a = vl.aovs.add(); a.name = an; a.type = 'COLOR'
    sc.use_nodes = True; nt = sc.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    rl = nt.nodes.new('CompositorNodeRLayers'); comp = nt.nodes.new('CompositorNodeComposite')
    nt.links.new(rl.outputs['Image'], comp.inputs['Image'])
    # hero variant 42 gains: champagne = 0.32 x fog glow (size 9) of AOV amber_glow (emit glare gain 0); blue = 0.6 x fog glow (size 6) of AOV blue_glow
    for aov, size, gain, stem in (("amber_glow", 9, 0.32, "champ"), ("blue_glow", 6, 0.6, "blue")):
        g = nt.nodes.new('CompositorNodeGlare'); g.glare_type = 'FOG_GLOW'; g.quality = 'HIGH'; g.threshold = 0.0; g.size = size; g.mix = 1.0
        nt.links.new(rl.outputs[aov], g.inputs['Image'])
        m = nt.nodes.new('CompositorNodeMixRGB'); m.blend_type = 'ADD'; m.inputs[0].default_value = gain; m.inputs[1].default_value = (0, 0, 0, 1)
        nt.links.new(g.outputs['Image'], m.inputs[2])
        fo = nt.nodes.new('CompositorNodeOutputFile'); fo.base_path = out; fo.format.file_format = 'PNG'; fo.format.color_mode = 'RGB'
        fo.format.color_depth = '16'; fo.file_slots[0].path = f"stage_6_glowraw_{stem}_"; nt.links.new(m.outputs['Image'], fo.inputs[0])
    r.filepath = f"{out}/stage_6_glowpass_beauty.png"; t0 = time.time(); bpy.ops.render.render(write_still=True)
    for stem in ("blue", "champ"):
        f = sorted(x for x in os.listdir(out) if x.startswith(f"stage_6_glowraw_{stem}_"))[-1]
        os.replace(f"{out}/{f}", f"{out}/stage_6_glowraw_{stem}.png")
    print("GLOW_DONE %.0fs" % (time.time() - t0), flush=True)

if argv and argv[0] == "build6": build6()
elif argv and argv[0] == "render6": render6(argv[1], int(argv[2]), int(argv[3]), int(argv[4]))
elif argv and argv[0] == "crops6":      # -- crops6 PREFIX x0:x1:y0:y1 ...  (1080x1440 frame, border crop, SPP env)
    r = prep(1080, 1440, int(os.environ.get("SPP", "64"))); r.use_border = True; r.use_crop_to_border = True
    for spec in argv[2:]:
        b = [float(x) for x in spec.split(":")]; r.border_min_x, r.border_max_x, r.border_min_y, r.border_max_y = b
        out = f"{argv[1]}_{spec.replace(':', '_')}.png"; t1 = time.time(); r.filepath = out; bpy.ops.render.render(write_still=True)
        print("CROP", out, "%.0fs" % (time.time() - t1), flush=True)
elif argv and argv[0] == "glow6": glow6(argv[1], int(argv[2]), int(argv[3]))
