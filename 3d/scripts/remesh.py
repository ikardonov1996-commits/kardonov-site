# Voxel-remesh the sculpture into one clean, closed, non-overlapping surface.
import bpy, sys, time
argv=sys.argv[sys.argv.index("--")+1:]
src, dst, voxel = argv[0], argv[1], float(argv[2])
bpy.ops.wm.open_mainfile(filepath=src)
ob=bpy.data.objects["Sculpture_HiRes"]; me=ob.data
t=time.time()
me.remesh_voxel_size=voxel; me.remesh_voxel_adaptivity=0.0; me.use_remesh_preserve_volume=True
bpy.context.view_layer.objects.active=ob; ob.select_set(True)
bpy.ops.object.voxel_remesh()
print("REMESH %.1fs polys=%d verts=%d"%(time.time()-t,len(ob.data.polygons),len(ob.data.vertices)))
ob.data.polygons.foreach_set('use_smooth',[True]*len(ob.data.polygons))
bpy.ops.wm.save_as_mainfile(filepath=dst,compress=True)
