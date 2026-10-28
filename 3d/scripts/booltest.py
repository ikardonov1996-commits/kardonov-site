import bpy, bmesh
O=bpy.data.objects; st=O["Sculpture_HiRes"]; blk=O["Marble_Block"]
bm=bmesh.new(); bm.from_mesh(blk.data)
print("block manifold:", all(e.is_manifold for e in bm.edges), "boundary edges:", sum(e.is_boundary for e in bm.edges), "faces", len(bm.faces))
print("block parent", blk.parent, "matrix", blk.matrix_world.translation, "statue", st.matrix_world.translation)
for solver, tol in (('EXACT',False),('EXACT',True),('FAST',False)):
    ob=st.copy(); ob.data=st.data.copy(); bpy.context.scene.collection.objects.link(ob); ob.modifiers.clear()
    for x in bpy.context.selected_objects: x.select_set(False)
    ob.select_set(True); bpy.context.view_layer.objects.active=ob
    ob.data.remesh_voxel_size=0.03; bpy.ops.object.voxel_remesh()
    b=ob.modifiers.new("I",'BOOLEAN'); b.operation='INTERSECT'; b.object=blk; b.solver=solver
    if solver=='EXACT': b.use_hole_tolerant=tol
    bpy.ops.object.modifier_apply(modifier=b.name); print(solver, tol, len(ob.data.polygons))
