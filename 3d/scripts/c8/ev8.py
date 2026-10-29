import bpy, sys, os, mathutils
sys.path.insert(0, "/tmp/claude-0/-home-user-kardonov-site/cb30cd45-1b88-5b9b-b3ff-480343f6cfce/scratchpad/scripts/c8")
from views import VIEWS
from glowcomp import setup_glow
argv=sys.argv[sys.argv.index("--")+1:]; pre=argv[0]; names=argv[1].split(","); res=argv[2] if len(argv)>2 else "600x800"
spp=int(argv[3]) if len(argv)>3 else 8
sc=bpy.context.scene; sc.render.engine='BLENDER_EEVEE_NEXT'; sc.eevee.taa_render_samples=spp
sc.render.resolution_x,sc.render.resolution_y=[int(v) for v in res.split("x")]; sc.render.resolution_percentage=100
sc.render.film_transparent=False; sc.render.image_settings.file_format='PNG'; sc.render.image_settings.color_mode='RGB'
if os.environ.get("NOSETUP")!="1": setup_glow(sc, amber_gain=float(os.environ.get("AGAIN","2.6")), amber_size=int(os.environ.get("ASIZE","9")))
wc=os.environ.get("WORLD")
if wc:
    c=[float(x) for x in wc.split(",")]; sc.world.node_tree.nodes["Background"].inputs[0].default_value=(*c,1)
cam=sc.camera
for n in names:
    out=pre+"_"+n+".png"
    if os.path.exists(out) and os.environ.get("FORCE")!="1": print("SKIP",n,flush=True); continue
    c,t,lens=VIEWS[n]; c=mathutils.Vector(c); t=mathutils.Vector(t)
    cam.location=c; cam.rotation_euler=(t-c).to_track_quat('-Z','Y').to_euler(); cam.data.type='PERSP'; cam.data.lens=lens; cam.data.clip_start=0.01
    sc.render.filepath=out+".tmp.png"; bpy.ops.render.render(write_still=True); os.replace(out+".tmp.png", out); print("RENDERED",n,flush=True)
