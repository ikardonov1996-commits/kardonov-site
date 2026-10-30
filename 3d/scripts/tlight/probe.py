import bpy
sc=bpy.context.scene
print("VT",sc.view_settings.view_transform,sc.view_settings.look,sc.view_settings.exposure,sc.view_settings.gamma)
w=sc.world; print("WORLD",w and w.name, w and w.use_nodes)
if w and w.use_nodes:
  for n in w.node_tree.nodes: print(" W",n.type,[ (i.name, getattr(i,'default_value',None) if not hasattr(getattr(i,'default_value',None),'__len__') else tuple(i.default_value)) for i in n.inputs if not i.is_linked][:3])
for o in sc.objects:
  if o.type=='LIGHT':
    l=o.data; print("L",o.name,l.type,tuple(round(c,3) for c in l.color),l.energy,getattr(l,'size',None),getattr(l,'shape',None),tuple(round(x,3) for x in o.location), getattr(l,'specular_factor',None), o.parent and o.parent.name)
print("CAM",sc.camera.name, sc.camera.data.lens)
for m in bpy.data.materials:
  if m.users==0: continue
  em=[]
  if m.use_nodes:
    for n in m.node_tree.nodes:
      if n.type in('EMISSION','BSDF_PRINCIPLED'):
        s=n.inputs.get('Emission Strength') or n.inputs.get('Strength')
        em.append((n.type,n.name, s and s.default_value))
  print("M",m.name,m.users,em)
for o in sc.objects:
  if o.type=='MESH': print("O",o.name,o.parent and o.parent.name,[s.material and s.material.name for s in o.material_slots], o.visible_camera)
