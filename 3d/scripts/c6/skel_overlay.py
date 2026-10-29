import bpy, sys, importlib, mathutils
sys.path.insert(0, "/tmp/claude-0/-home-user-kardonov-site/cb30cd45-1b88-5b9b-b3ff-480343f6cfce/scratchpad/scripts/c6")
import hand_skel; importlib.reload(hand_skel)
V=mathutils.Vector
cols={"Index":(1,0,0,1),"Middle":(0,1,0,1),"Ring":(0,0.4,1,1),"Pinky":(1,1,0,1),"Thumb":(1,0,1,1)}
for nm,pts in hand_skel.FINGERS.items():
    m=bpy.data.materials.new(nm); m.diffuse_color=cols[nm]
    cu=bpy.data.curves.new(nm,'CURVE'); cu.dimensions='3D'; sp=cu.splines.new('POLY'); sp.points.add(len(pts))
    for p,q in zip(sp.points,[hand_skel.WRIST]+pts): p.co=(*q,1)
    cu.bevel_depth=0.0012; cu.materials.append(m)
    o=bpy.data.objects.new("SK_"+nm,cu); bpy.context.scene.collection.objects.link(o)
    for q in pts:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.0022, location=q); s=bpy.context.object; s.name="SK_s"; s.data.materials.append(m)
a=bpy.data.objects["ArmRef"]; mm=bpy.data.materials.new("mar"); mm.diffuse_color=(0.8,0.8,0.8,0.35); mm.blend_method='BLEND'
a.data.materials.clear(); a.data.materials.append(mm)
