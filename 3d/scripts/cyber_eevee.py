# EEVEE preview renders: args out_prefix "name:cam:target:lens;..." [WxH] [glare=1]
import bpy, sys, mathutils
argv=sys.argv[sys.argv.index("--")+1:]
pre=argv[0]; views=argv[1].split(";"); res=argv[2] if len(argv)>2 else "600x800"
glare = len(argv)>3 and argv[3]=="1"
sc=bpy.context.scene
sc.render.engine='BLENDER_EEVEE_NEXT'; sc.eevee.taa_render_samples=8
sc.render.resolution_x,sc.render.resolution_y=[int(v) for v in res.split("x")]; sc.render.resolution_percentage=100
sc.render.film_transparent=False
sc.render.image_settings.file_format='PNG'; sc.render.image_settings.color_mode='RGB'
if glare:
    sc.use_nodes=True; nt=sc.node_tree
    rl=[n for n in nt.nodes if n.type=='R_LAYERS'][0]; comp=[n for n in nt.nodes if n.type=='COMPOSITE'][0]
    g=nt.nodes.new('CompositorNodeGlare'); g.glare_type='FOG_GLOW'; g.quality='MEDIUM'; g.threshold=2.5; g.size=7; g.mix=-0.6
    nt.links.new(rl.outputs['Image'], g.inputs['Image']); nt.links.new(g.outputs['Image'], comp.inputs['Image'])
cam=sc.camera
for v in views:
    p=v.split(":"); name=p[0]
    c=mathutils.Vector([float(x) for x in p[1].split(",")]); t=mathutils.Vector([float(x) for x in p[2].split(",")])
    cam.location=c; cam.rotation_euler=(t-c).to_track_quat('-Z','Y').to_euler()
    cam.data.type='PERSP'; cam.data.lens=float(p[3]); cam.data.clip_start=0.01
    sc.render.filepath=pre+"_"+name+".png"; bpy.ops.render.render(write_still=True)
    print("RENDERED", name, flush=True)
