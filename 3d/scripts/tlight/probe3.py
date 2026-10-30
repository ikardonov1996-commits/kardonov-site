import bpy
t=bpy.data.materials['AI_Titanium'].node_tree
for n in t.nodes:
  if n.type=='RGB': print("RGB",tuple(round(x,3) for x in n.outputs[0].default_value))
  if n.type=='MAP_RANGE': print("MR",n.name,[round(n.inputs[i].default_value,3) for i in (1,2,3,4)])
  if n.type=='MATH': print("MATH",n.name,n.operation,[round(i.default_value,3) for i in n.inputs if not i.is_linked])
