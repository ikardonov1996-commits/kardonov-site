import bpy, sys, mathutils
sys.path.insert(0, "/tmp/claude-0/-home-user-kardonov-site/cb30cd45-1b88-5b9b-b3ff-480343f6cfce/scratchpad/scripts/c2")
from views import VIEWS
argv=sys.argv[sys.argv.index("--")+1:]; pre=argv[0]; names=argv[1].split(","); res=argv[2] if len(argv)>2 else "450x600"
sc=bpy.context.scene; sc.render.engine='BLENDER_WORKBENCH'
sc.display.shading.light='STUDIO'; sc.display.shading.color_type='MATERIAL'; sc.display.shading.show_cavity=True
sc.render.resolution_x,sc.render.resolution_y=[int(v) for v in res.split("x")]; sc.render.resolution_percentage=100
for o in bpy.data.objects:
    if o.name=="Floor": o.hide_render=True
cam=sc.camera
for n in names:
    c,t,lens=VIEWS[n]; c=mathutils.Vector(c); t=mathutils.Vector(t)
    cam.location=c; cam.rotation_euler=(t-c).to_track_quat('-Z','Y').to_euler(); cam.data.type='PERSP'; cam.data.lens=lens; cam.data.clip_start=0.01
    sc.render.filepath=pre+"_"+n+".png"; bpy.ops.render.render(write_still=True)
