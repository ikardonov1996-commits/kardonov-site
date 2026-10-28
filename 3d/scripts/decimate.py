# Reduce polycount with collapse decimation (keeps detail where curvature is high).
import bpy, sys, time
argv=sys.argv[sys.argv.index("--")+1:]
src, dst, ratio = argv[0], argv[1], float(argv[2])
bpy.ops.wm.open_mainfile(filepath=src)
ob=bpy.data.objects["Sculpture_HiRes"]
bpy.context.view_layer.objects.active=ob
t=time.time()
m=ob.modifiers.new("Decimate",'DECIMATE'); m.decimate_type='COLLAPSE'; m.ratio=ratio; m.use_collapse_triangulate=True
bpy.ops.object.modifier_apply(modifier=m.name)
ob.data.polygons.foreach_set('use_smooth',[True]*len(ob.data.polygons))
print("DECIMATED %.0fs polys=%d"%(time.time()-t,len(ob.data.polygons)))
bpy.ops.wm.save_as_mainfile(filepath=dst,compress=True)
