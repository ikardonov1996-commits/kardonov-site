# Windlass v4: axle (whole object; only its ends between post/collar/boss are visible, middle sits inside drum & posts)
# + Axle_Collar_R + Axle_Collar_L -> AI_Titanium v3. Drum_Band_* stay Iron_Dark. Backup of v3 state: scene_rope_windlass_v3.blend
import bpy, sys
sys.path.append("/tmp/claude-0/-home-user-kardonov-site/cb30cd45-1b88-5b9b-b3ff-480343f6cfce/scratchpad/scripts")
from mat_ai_titanium import ai_titanium
m = ai_titanium(); O = bpy.data.objects
for n in ("Axle", "Axle_Collar_R", "Axle_Collar_L"):
    O[n]["ti_grain_dir"] = (1.0, 0.0, 0.0)            # along the axle (local X)
    for s in O[n].material_slots: s.material = m
for n in ("Axle", "Axle_Collar_R", "Axle_Collar_L", "Crank", "Crank_Boss", "Crank_Grip"): print("MATS", n, [s.material.name for s in O[n].material_slots])
print("IRON_LEFT", [o.name for o in O if any(s.material and s.material.name == "Iron_Dark" for s in o.material_slots)])
print("MATLIST", [x.name for x in bpy.data.materials])
bpy.ops.wm.save_mainfile(compress=True); print("SAVED")
