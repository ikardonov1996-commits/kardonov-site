# Flat marble swatch scene for fast pattern iteration (no sculpture mesh).
# usage: blender -b SRC.blend -P swatch.py -- OUT.blend
import bpy, sys
from mathutils import Vector
argv=sys.argv[sys.argv.index("--")+1:]
SIZE=float(argv[1]) if len(argv)>1 else 0.6
sc=bpy.context.scene
for o in list(bpy.data.objects):
    if o.name not in ("MarbleSpace","Camera","Key","Fill","Rim"): bpy.data.objects.remove(o)
m=bpy.data.materials["Marble"]
def slab(name,loc,rot,size):
    bpy.ops.mesh.primitive_plane_add(size=1,location=loc,rotation=rot); p=bpy.context.active_object
    p.name=name; p.scale=(size[0],size[1],1); p.data.materials.append(m); p["polish"]=1.0; p["gold"]=0.0
    return p
# a 60x60 cm vertical slab through the sculpture's chest, facing the camera (-Y)
slab("Swatch",(0,-0.03,0.6),(1.5708,0,0),(SIZE,SIZE))
cam=sc.camera; cam.data.type='ORTHO'; cam.data.ortho_scale=SIZE; cam.location=(0,-2,0.6); cam.rotation_euler=(1.5708,0,0)
for nm in ("Key","Fill","Rim"):
    l=bpy.data.objects[nm]; l.location=(l.location.x,-abs(l.location.y)-0.5,l.location.z)
sc.render.resolution_x=900; sc.render.resolution_y=900
sc.render.engine='BLENDER_EEVEE_NEXT'; sc.eevee.taa_render_samples=16
bpy.ops.wm.save_as_mainfile(filepath=argv[0])
