import bpy
def dump(nt, pre=""):
  for n in nt.nodes:
    vals=[]
    for i in n.inputs:
      if i.is_linked: vals.append((i.name,"<L>")); continue
      v=getattr(i,'default_value',None)
      if v is None: continue
      try: v=tuple(round(x,3) for x in v)
      except TypeError: v=round(v,3) if isinstance(v,float) else v
      if i.name in ('Base Color','Metallic','Roughness','Emission Color','Emission Strength','Color','Strength','Coat Weight','Specular IOR Level','Subsurface Weight','Anisotropic','Fac','Factor','A','B','Scale'): vals.append((i.name,v))
    extra=""
    if n.type=='VALTORGB': extra=[(round(e.position,3),tuple(round(c,3) for c in e.color)) for e in n.color_ramp.elements]
    if n.type=='GROUP': extra=n.node_tree.name
    print(pre,n.name,n.type,vals,extra)
  for l in nt.links: print(pre,"  ",l.from_node.name,l.from_socket.name,"->",l.to_node.name,l.to_socket.name)
w=bpy.context.scene.world; print("== WORLD"); dump(w.node_tree)
for m in ['AI_Titanium','Marble','Tool_Gold','Tool_Steel','Tool_GlowBlue','Tool_GlowBlueRing','Tool_GlowAmber','Tool_Leather','Tool_Bronze','Tool_GunmetalDark']:
  print("== ",m); dump(bpy.data.materials[m].node_tree)
