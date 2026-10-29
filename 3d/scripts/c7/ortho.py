# ortho workbench renders of given objects around a box, with world grid info printed
import bpy, sys, math, mathutils
argv=sys.argv[sys.argv.index("--")+1:]; out=argv[0]; objs=argv[1].split(","); cx,cy,cz,size=[float(v) for v in argv[2].split(",")]
views=argv[3].split(",") if len(argv)>3 else ["-Y","-X","+Y","+X"]
sc=bpy.context.scene; sc.render.engine='BLENDER_WORKBENCH'; sc.render.use_compositing=False
sc.display.shading.light='STUDIO'; sc.display.shading.color_type='MATERIAL' if len(argv)>4 else 'SINGLE'; sc.display.shading.single_color=(0.8,0.8,0.8)
sc.display.shading.show_cavity=True
if len(argv)>4: sc.display.shading.show_xray=True; sc.display.shading.xray_alpha=0.45
sc.render.resolution_x=sc.render.resolution_y=800; sc.render.film_transparent=False
sc.world.color=(0.05,0.05,0.06)
for o in sc.objects:
    if o.type in('MESH','CURVE'): o.hide_render = not any(o.name.startswith(n) for n in objs)
cam=sc.camera; cam.data.type='ORTHO'; cam.data.ortho_scale=size; cam.data.clip_start=0.001; cam.data.clip_end=10
C=mathutils.Vector((cx,cy,cz))
for v in views:
    ax={'X':0,'Y':1,'Z':2}[v[1]]; d=mathutils.Vector((0,0,0)); d[ax]=1 if v[0]=='+' else -1
    cam.location=C+d*1.0; up=(0,0,1) if ax!=2 else (0,1,0)
    cam.rotation_euler=(-d).to_track_quat('-Z','Y' if ax!=2 else 'Y').to_euler()
    sc.render.filepath=out+"_"+v.replace('+','p').replace('-','m')+".png"; bpy.ops.render.render(write_still=True)
