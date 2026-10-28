# Verify veins stay locked: move/rotate Marble_Root and compare texture coordinate of a block vertex.
import bpy
from mathutils import Matrix
O=bpy.data.objects; blk=O["Marble_Block"]; sp=O["MarbleSpace"]; root=O["Marble_Root"]
v=blk.data.vertices[123].co
def tex(): return sp.matrix_world.inverted() @ (blk.matrix_world @ v)
a=tex(); root.location=(1.0,2.0,-0.5); root.rotation_euler=(0.1,0.2,0.7); bpy.context.view_layer.update(); b=tex()
print("VEIN COORD before", tuple(round(x,5) for x in a), "after", tuple(round(x,5) for x in b))
