import bpy
O=bpy.data.objects
for m in bpy.data.materials:
    if not m.use_nodes: continue
    b=[n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED']
    s=""
    for n in b:
        bc=n.inputs['Base Color']; s+=f" base={tuple(round(x,3) for x in bc.default_value) if not bc.is_linked else 'LINK'} metal={n.inputs['Metallic'].default_value:.2f} rough={n.inputs['Roughness'].default_value if not n.inputs['Roughness'].is_linked else 'LINK'}"
    print("MAT",m.name,m.users,s)
for n in ("Rope_FreeSpan","Rope_DrumCoil","Sling_A","Rope_Lashing"):
    o=O[n]; print("MOD",n,[(md.type,md.name) for md in o.modifiers], o.data.materials[:] if hasattr(o.data,'materials') else '')
d=O["Drum"]; print("DRV",[ (f.data_path,f.driver.expression) for f in d.animation_data.drivers] if d.animation_data else None)
for n in ("Hang_Pivot","Hang_Drop","Descent_Control","Rope_FreeSpan"):
    o=O[n]; ad=o.animation_data
    print("ANIM",n, [(f.data_path,f.array_index,len(f.keyframe_points)) for f in ad.action.fcurves] if ad and ad.action else None, [ (f.data_path,f.driver.expression) for f in ad.drivers] if ad else None)
