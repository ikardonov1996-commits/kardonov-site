import bpy, sys
argv=sys.argv[sys.argv.index("--")+1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=argv[0])
for o in bpy.data.objects:
    d=o.data
    print(o.name,o.type, getattr(d,'name',None), len(d.polygons) if o.type=='MESH' else '', len(d.vertices) if o.type=='MESH' else '', tuple(round(x,3) for x in o.dimensions), o.location[:], o.rotation_euler[:], o.parent.name if o.parent else None)
    if o.type=='MESH': print('  mats',[m.name if m else None for m in d.materials],'uv',len(d.uv_layers),'colattr',[a.name for a in d.color_attributes])
for i in bpy.data.images: print('IMG',i.name,i.size[:])
