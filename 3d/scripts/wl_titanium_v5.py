# Windlass v5: Drum_Band_L/R/FL/FR (dark iron rings at drum ends / flanges) -> AI_Titanium v3.
# Optional (arg "axle"): the hidden middle of the Axle (inside drum/posts, kept Iron_Dark in v4b) -> titanium too,
# so Iron_Dark has no users left. Backup of v4 state: scene_rope_windlass_v4.blend
# usage: blender -b scene_rope_windlass.blend -P wl_titanium_v5.py -- [axle] [nosave]
import bpy, sys
sys.path.append("/tmp/claude-0/-home-user-kardonov-site/cb30cd45-1b88-5b9b-b3ff-480343f6cfce/scratchpad/scripts")
from mat_ai_titanium import ai_titanium
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
m = ai_titanium(); O = bpy.data.objects
for n in ("Drum_Band_L", "Drum_Band_R", "Drum_Band_FL", "Drum_Band_FR"):
    O[n]["ti_grain_dir"] = (1.0, 0.0, 0.0)   # local X = drum/axle axis: grain across the band, machining rings run round it (turned ring)
    for s in O[n].material_slots: s.material = m
if "axle" in args:
    me = O["Axle"].data
    for i in range(len(me.materials)): me.materials[i] = m
    for p in me.polygons: p.material_index = 0
    while len(me.materials) > 1: me.materials.pop(index=len(me.materials) - 1)
for o in O:
    if o.type in ('MESH', 'CURVE') and o.parent and o.parent.name in ("Drum", "Windlass"):
        print("MATS", o.name, [s.material.name if s.material else None for s in o.material_slots], o.get("ti_grain_dir") and tuple(o["ti_grain_dir"]))
print("IRON_LEFT", [o.name for o in O if any(s.material and s.material.name == "Iron_Dark" for s in o.material_slots)])
if "nosave" not in args: bpy.ops.wm.save_mainfile(compress=True); print("SAVED")
else: bpy.ops.wm.save_as_mainfile(filepath=args[-1], compress=True, copy=True); print("SAVED COPY", args[-1])
