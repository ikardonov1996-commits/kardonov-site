# Windlass: crank grip -> shared AI_Titanium (saves scene_rope_windlass.blend; backup = scene_rope_windlass_v1.blend)
import bpy, sys
sys.path.append("/tmp/claude-0/-home-user-kardonov-site/cb30cd45-1b88-5b9b-b3ff-480343f6cfce/scratchpad/scripts")
from mat_ai_titanium import ai_titanium
m = ai_titanium(); g = bpy.data.objects["Crank_Grip"]
for s in g.material_slots: s.link = 'OBJECT' if False else s.link; s.material = m
print("GRIP", [s.material.name for s in g.material_slots])
bpy.ops.wm.save_mainfile(compress=True)
