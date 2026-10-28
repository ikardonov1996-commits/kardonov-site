import bpy
for o in bpy.data.objects:
    print(o.name, o.type, o.parent.name if o.parent else None, o.hide_render, tuple(round(v,3) for v in o.matrix_world.translation), tuple(round(v,3) for v in o.scale))
s=bpy.data.objects["Sculpture_HiRes"]; print(s.matrix_world); print([m.name for m in s.data.materials]); print(len(s.data.vertices))
sc=bpy.context.scene; print(sc.render.engine, sc.camera, [c.name for c in sc.collection.children])
w=sc.world; print(w.name if w else None)
