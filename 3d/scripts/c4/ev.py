import bpy, sys, os, mathutils
sys.path.insert(0, "/tmp/claude-0/-home-user-kardonov-site/cb30cd45-1b88-5b9b-b3ff-480343f6cfce/scratchpad/scripts/c4")
from views import VIEWS
from glowcomp import setup_glow
argv=sys.argv[sys.argv.index("--")+1:]; pre=argv[0]; names=argv[1].split(","); res=argv[2] if len(argv)>2 else "600x800"
spp=int(argv[3]) if len(argv)>3 else 8
sc=bpy.context.scene; sc.render.engine='BLENDER_EEVEE_NEXT'; sc.eevee.taa_render_samples=spp
sc.render.resolution_x,sc.render.resolution_y=[int(v) for v in res.split("x")]; sc.render.resolution_percentage=100
sc.render.film_transparent=False; sc.render.image_settings.file_format='PNG'; sc.render.image_settings.color_mode='RGB'
setup_glow(sc, float(os.environ.get("GGAIN","1.0")), float(os.environ.get("GTHR","0.4")))
cam=sc.camera
for n in names:
    c,t,lens=VIEWS[n]; c=mathutils.Vector(c); t=mathutils.Vector(t)
    cam.location=c; cam.rotation_euler=(t-c).to_track_quat('-Z','Y').to_euler(); cam.data.type='PERSP'; cam.data.lens=lens; cam.data.clip_start=0.01
    sc.render.filepath=pre+"_"+n+".png"; bpy.ops.render.render(write_still=True); print("RENDERED",n,flush=True)
