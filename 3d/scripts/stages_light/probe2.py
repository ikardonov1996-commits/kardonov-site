import bpy
from mathutils import Vector as V
sc=bpy.context.scene; O=bpy.data.objects
names=["Marble_Block","C1_Pitched","C3_Relief2","C4_Freed","C5_Point","C6_Claw","Sculpture_HiRes"]
for i,f in enumerate(sc["stage_frames"]):
    sc.frame_set(f); n=names[i]; o=O[n]
    dg=bpy.context.evaluated_depsgraph_get(); oe=o.evaluated_get(dg)
    bb=[oe.matrix_world@V(c) for c in oe.bound_box]
    print(f,n,"hide_render",o.hide_render,"vis",[x for x in names if not O[x].hide_render], "scale",tuple(round(x,3) for x in o.matrix_world.to_scale()),"bbz",round(min(b.z for b in bb),3),round(max(b.z for b in bb),3),"bbx",round(min(b.x for b in bb),3),round(max(b.x for b in bb),3), "verts_eval", len(oe.data.vertices))
    print("  Floor", O["Floor"].matrix_world.translation[:], "root", O["Marble_Root"].matrix_world.translation[:])
for m in bpy.data.materials: print("MAT",m.name,m.users)
m=bpy.data.materials["Marble_Carve"]
for nd in m.node_tree.nodes:
    ins=[(i.name, (tuple(i.default_value) if hasattr(i.default_value,'__len__') else round(i.default_value,4))) for i in nd.inputs if hasattr(i,'default_value') and not i.is_linked][:12]
    print(" N",nd.type,nd.name,ins if nd.type in('BSDF_PRINCIPLED','DISPLACEMENT','BUMP','VALTORGB','MIX') else "")
print("disp", m.cycles.displacement_method if hasattr(m.cycles,'displacement_method') else m.displacement_method)
