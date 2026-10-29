import bpy, sys, mathutils
sys.path.insert(0, "/tmp/claude-0/-home-user-kardonov-site/cb30cd45-1b88-5b9b-b3ff-480343f6cfce/scratchpad/scripts/c6")
from views import VIEWS
argv=sys.argv[sys.argv.index("--")+1:]; pre=argv[0]; names=argv[1].split(",")
sc=bpy.context.scene; sc.render.engine='BLENDER_WORKBENCH'; sc.render.use_compositing=False
sc.display.shading.light='STUDIO'; sc.display.shading.color_type='MATERIAL'; sc.display.shading.show_cavity=True
sc.render.resolution_x,sc.render.resolution_y=600,800
for m in bpy.data.materials:
    if m.name=="AI_Titanium": m.diffuse_color=(0.85,0.87,0.9,1)
cam=sc.camera
for n in names:
    c,t,lens=VIEWS[n]; c=mathutils.Vector(c); t=mathutils.Vector(t)
    cam.location=c; cam.rotation_euler=(t-c).to_track_quat('-Z','Y').to_euler(); cam.data.type='PERSP'; cam.data.lens=lens; cam.data.clip_start=0.01
    sc.render.filepath=pre+"_"+n+".png"; bpy.ops.render.render(write_still=True)
