import bpy
for o in bpy.data.objects:
    if o.type=='MESH': print("OBJ", o.name, len(o.data.polygons), "hide_render", o.hide_render, [round(x,2) for x in o.dimensions])
