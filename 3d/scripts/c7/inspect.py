import bpy
for o in bpy.data.objects:
    if o.name.startswith(("Robo_","Neuro_")): continue
    print(o.name,o.type,[m.name for m in getattr(o.data,'materials',[]) or []] if o.type=='MESH' else (o.data.type if o.type=='LIGHT' else ''), tuple(round(v,2) for v in o.location), o.visible_camera if hasattr(o,'visible_camera') else '')
    if o.type=='LIGHT': print('   E',o.data.energy, tuple(o.data.color), getattr(o.data,'size',None))
sc=bpy.context.scene; print(sc.render.engine, sc.view_settings.view_transform, sc.view_settings.look, sc.eevee.use_raytracing if hasattr(sc.eevee,'use_raytracing') else '')
for o in bpy.data.objects:
    if o.name.startswith(("Robo_Glow","Robo_Shoulder","Robo_Hand")): print(o.name)
