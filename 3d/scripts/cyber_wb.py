# Workbench shape renders: args: out_prefix view1;view2... each view "name:cx,cy,cz:tx,ty,tz:lens[:ortho_scale]"
import bpy, sys, mathutils
argv=sys.argv[sys.argv.index("--")+1:]
pre=argv[0]; views=argv[1].split(";")
res=argv[2] if len(argv)>2 else "600x800"
sc=bpy.context.scene
sc.render.engine='BLENDER_WORKBENCH'
sc.display.shading.light='STUDIO'; sc.display.shading.color_type='MATERIAL' if 'mat' in pre else 'OBJECT'
sc.display.shading.show_cavity=True
sc.render.resolution_x,sc.render.resolution_y=[int(v) for v in res.split("x")]
sc.render.resolution_percentage=100
for o in bpy.data.objects:
    if o.name=="Floor": o.hide_render=True
cam=sc.camera
for v in views:
    p=v.split(":"); name=p[0]
    c=mathutils.Vector([float(x) for x in p[1].split(",")]); t=mathutils.Vector([float(x) for x in p[2].split(",")])
    cam.location=c; cam.rotation_euler=(t-c).to_track_quat('-Z','Y').to_euler()
    if len(p)>4: cam.data.type='ORTHO'; cam.data.ortho_scale=float(p[4])
    else: cam.data.type='PERSP'; cam.data.lens=float(p[3])
    cam.data.clip_start=0.01
    sc.render.filepath=pre+"_"+name+".png"; bpy.ops.render.render(write_still=True)
