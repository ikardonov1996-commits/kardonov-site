import bpy
sc=bpy.context.scene
for o in bpy.data.objects:
    print("OBJ", o.name, o.type, "parent=", o.parent.name if o.parent else None, tuple(round(x,3) for x in o.matrix_world.translation), "anim" if o.animation_data else "")
print("CAM", sc.camera.name, sc.render.resolution_x, sc.render.resolution_y, sc.render.engine, sc.frame_start, sc.frame_end)
