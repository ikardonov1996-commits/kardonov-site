import bpy,sys
argv=sys.argv[sys.argv.index("--")+1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
sc=bpy.context.scene; m=bpy.data.materials["Marble"]; nt=m.node_tree
out=[n for n in nt.nodes if n.type=='OUTPUT_MATERIAL'][0]
r=[n for n in nt.nodes if n.label=='Main veins'][0]
em=nt.nodes.new('ShaderNodeEmission'); nt.links.new(r.outputs['Color'],em.inputs[0]); nt.links.new(em.outputs[0],out.inputs['Surface'])
sc.cycles.samples=8; sc.render.resolution_percentage=50
sc.render.filepath=argv[1]; bpy.ops.render.render(write_still=True)
