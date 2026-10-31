import bpy
from mathutils import Vector
sc=bpy.context.scene; O=bpy.data.objects
print("ENGINE",sc.render.engine, sc.view_settings.view_transform, sc.view_settings.look, sc.view_settings.exposure)
print("CAM",sc.camera.name if sc.camera else None)
dg=bpy.context.evaluated_depsgraph_get()
for o in O:
    if o.type in('MESH','CURVE'):
        e=o.evaluated_get(dg); pts=[e.matrix_world@Vector(c) for c in e.bound_box]
        mn=[min(p[i] for p in pts) for i in range(3)]; mx=[max(p[i] for p in pts) for i in range(3)]
        print("OBJ",o.name,o.type,"par=",o.parent.name if o.parent else None,"mn",[round(x,3) for x in mn],"mx",[round(x,3) for x in mx],"mats",[s.material.name for s in o.material_slots if s.material])
    else:
        print("OBJ",o.name,o.type,"par=",o.parent.name if o.parent else None,"loc",[round(x,3) for x in o.matrix_world.translation], (o.data.energy if o.type=='LIGHT' else ''))
w=sc.world
print("WORLD",w.name if w else None, [ (n.type, n.inputs[1].default_value if n.type=='BACKGROUND' else '') for n in w.node_tree.nodes] if w and w.use_nodes else '')
ctl=O["Descent_Control"]; print("descent",ctl["descent"], ctl.animation_data)
print("frames",sc.frame_start,sc.frame_end)
