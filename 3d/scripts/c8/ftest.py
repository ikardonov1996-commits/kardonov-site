import bpy
b=bpy.data.materials['Floor_Dark'].node_tree.nodes['Principled BSDF']
b.inputs["Specular IOR Level"].default_value=0.0; b.inputs["Roughness"].default_value=0.9
