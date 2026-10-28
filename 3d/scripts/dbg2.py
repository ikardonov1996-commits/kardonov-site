import bpy, bmesh
O=bpy.data.objects
def vol(ob):
    b=bmesh.new(); b.from_mesh(ob.data); v=b.calc_volume(signed=True); b.free(); return v
C1=O["C1_Pitched"]; U=O["DBG_U"]
def test(op, solver, a, b, **kw):
    ob=a.copy(); ob.data=a.data.copy(); bpy.context.scene.collection.objects.link(ob); ob.modifiers.clear()
    for x in bpy.context.selected_objects: x.select_set(False)
    ob.select_set(True); bpy.context.view_layer.objects.active=ob
    m=ob.modifiers.new("B",'BOOLEAN'); m.operation=op; m.object=b; m.solver=solver
    for k,v in kw.items(): setattr(m,k,v)
    bpy.ops.object.modifier_apply(modifier=m.name); print(op, solver, kw, "vol", round(vol(ob),4), len(ob.data.polygons))
print("C1 parent", C1.parent, "U parent", U.parent, C1.matrix_world.translation, U.matrix_world.translation)
test('INTERSECT','FAST',C1,U)
test('INTERSECT','EXACT',C1,U,use_hole_tolerant=True)
test('INTERSECT','EXACT',U,C1)
