import bpy
sc=bpy.context.scene
print("FILE",bpy.data.filepath, "frame",sc.frame_current, dict(sc.items()).keys() if hasattr(sc,'items') else '')
if "stage_frames" in sc: print("stage_frames", list(sc["stage_frames"]))
print("cam", sc.camera and sc.camera.name, sc.camera and tuple(sc.camera.matrix_world.translation))
for o in bpy.data.objects:
    if o.type in ('MESH','CURVE','EMPTY'):
        n=len(o.data.vertices) if o.type=='MESH' else 0
        print(f"{o.name:34s} {o.type:5s} v={n:8d} par={o.parent.name if o.parent else '-':20s} loc={tuple(round(x,4) for x in o.matrix_world.translation)} rot={tuple(round(x,4) for x in o.matrix_world.to_euler())} sc={tuple(round(x,4) for x in o.matrix_world.to_scale())} mats={[m.name for m in o.data.materials if m] if o.type!='EMPTY' else ''} hr={o.hide_render} anim={bool(o.animation_data and o.animation_data.action)} mods={[m.type for m in o.modifiers]} colls={[c.name for c in o.users_collection]}")
