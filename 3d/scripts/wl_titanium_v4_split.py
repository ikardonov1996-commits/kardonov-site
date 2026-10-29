# Windlass v4b: Axle split by faces -- titanium only on the visible ends (outside the posts, |world x| > 0.70),
# middle part inside drum/posts stays Iron_Dark (otherwise it shows through the rope-plane cut of windlass_back_NN).
import bpy, bmesh
from mathutils import Vector
O = bpy.data.objects; ax = O["Axle"]; me = ax.data
print("BEVEL", [(m.limit_method, round(m.width, 4), m.segments) for m in ax.modifiers if m.type == 'BEVEL'])
iron, ti = bpy.data.materials["Iron_Dark"], bpy.data.materials["AI_Titanium"]
if len(me.materials) < 2: me.materials.append(iron)
me.materials[0] = ti; me.materials[1] = iron
mw, inv = ax.matrix_world, ax.matrix_world.inverted()
bm = bmesh.new(); bm.from_mesh(me)
for wx in (-0.70, 0.70):
    co = inv @ Vector((wx, mw.translation.y, mw.translation.z)); no = (inv.to_3x3() @ Vector((1, 0, 0))).normalized()
    geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
    bmesh.ops.bisect_plane(bm, geom=geom, plane_co=co, plane_no=no)
n_iron = 0
for f in bm.faces:
    x = (mw @ f.calc_center_median()).x
    f.material_index = 1 if abs(x) < 0.70 else 0; n_iron += f.material_index
bm.to_mesh(me); bm.free(); me.update()
print("AXLE faces", len(me.polygons), "iron", n_iron, "slots", [s.material.name for s in ax.material_slots])
bpy.ops.wm.save_mainfile(compress=True); print("SAVED")
