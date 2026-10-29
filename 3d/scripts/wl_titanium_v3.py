# Windlass v3: crank lever (curve "Crank") + crank hub ("Crank_Boss") -> AI_Titanium v3; Crank_Grip back to wood.
# saves scene_rope_windlass.blend (backups: _v1 = original, _v2grip = titanium grip state)
import bpy, sys
sys.path.append("/tmp/claude-0/-home-user-kardonov-site/cb30cd45-1b88-5b9b-b3ff-480343f6cfce/scratchpad/scripts")
from mat_ai_titanium import ai_titanium
m = ai_titanium(); O = bpy.data.objects; wood = bpy.data.materials["Wood_Aged"]
for s in O["Crank_Grip"].material_slots: s.material = wood
O["Crank"]["ti_grain_dir"] = (0.0, 0.0, 1.0)        # long vertical arm (drum-local Z)
O["Crank_Boss"]["ti_grain_dir"] = (1.0, 0.0, 0.0)   # along the axle
for n in ("Crank", "Crank_Boss"):
    for s in O[n].material_slots: s.material = m
for n in ("Crank", "Crank_Boss", "Crank_Grip"): print("MATS", n, [s.material.name for s in O[n].material_slots])
print("IRON_LEFT", [o.name for o in O if any(s.material and s.material.name == "Iron_Dark" for s in o.material_slots)])
bpy.ops.wm.save_mainfile(compress=True); print("SAVED")
