import bpy
from mathutils import Vector as V
sc=bpy.context.scene; O=bpy.data.objects
print("FRAMES", list(sc.get("stage_frames",[])), sc.frame_current, "cam", sc.camera.name if sc.camera else None)
print("VIEW", sc.view_settings.view_transform, sc.view_settings.look, sc.view_settings.exposure, "world", sc.world.name if sc.world else None)
if sc.world and sc.world.use_nodes:
    for n in sc.world.node_tree.nodes: print("  WN", n.type, n.name, [ (i.name, tuple(i.default_value) if hasattr(i.default_value,'__len__') else i.default_value) for i in n.inputs if hasattr(i,'default_value')][:3])
for o in O:
    if o.type in ('MESH','LIGHT','CAMERA','EMPTY'):
        bb=[o.matrix_world@V(c) for c in o.bound_box]
        mn=V((min(b.x for b in bb),min(b.y for b in bb),min(b.z for b in bb))); mx=V((max(b.x for b in bb),max(b.y for b in bb),max(b.z for b in bb)))
        extra=""
        if o.type=='LIGHT': extra=f"{o.data.type} E={o.data.energy} col={tuple(o.data.color)} size={getattr(o.data,'size',None)}"
        if o.type=='CAMERA': extra=f"lens={o.data.lens} fit={o.data.sensor_fit} sw={o.data.sensor_width} shift={o.data.shift_x},{o.data.shift_y} rot={tuple(o.rotation_euler)}"
        if o.type=='MESH': extra=f"mats={[m.name for m in o.data.materials if m]} v={len(o.data.vertices)} hr={o.hide_render} mods={[m.type for m in o.modifiers]}"
        print(o.type,o.name,"par",o.parent.name if o.parent else None,"loc",tuple(round(x,3) for x in o.location),"bb",tuple(round(x,3) for x in mn),tuple(round(x,3) for x in mx),extra)
print("ANIM", [ (o.name) for o in O if o.animation_data and o.animation_data.action])
