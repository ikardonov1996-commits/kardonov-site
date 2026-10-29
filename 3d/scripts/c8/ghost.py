import bpy
with bpy.data.libraries.load("/tmp/claude-0/-home-user-kardonov-site/cb30cd45-1b88-5b9b-b3ff-480343f6cfce/scratchpad/out/cyber/stage_cut.blend") as (s, d): d.objects = ["ArmRef"]
o = d.objects[0]; bpy.context.scene.collection.objects.link(o)
m = bpy.data.materials.new("ghost"); m.diffuse_color = (1.0, 0.75, 0.5, 0.25); o.data.materials.clear(); o.data.materials.append(m)
for mm in bpy.data.materials:
    if mm.name.startswith("AI_Titanium") and mm.name != "AI_Titanium_Joint": mm.diffuse_color = (0.85, 0.87, 0.9, 1)
