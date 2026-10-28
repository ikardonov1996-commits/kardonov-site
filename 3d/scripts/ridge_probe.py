# Render raw ridged-multifractal values on the swatch (emission, value/4) to see their range.
import bpy, sys
argv=sys.argv[sys.argv.index("--")+1:]
m=bpy.data.materials["Marble"]; nt=m.node_tree; N=nt.nodes; L=nt.links; N.clear()
tc=N.new('ShaderNodeTexCoord'); tc.object=bpy.data.objects["MarbleSpace"]
st=N.new('ShaderNodeVectorMath'); st.operation='MULTIPLY'; st.inputs[1].default_value=(1,0.35,1); L.new(tc.outputs['Object'],st.inputs[0])
nz=N.new('ShaderNodeTexNoise'); nz.noise_type='RIDGED_MULTIFRACTAL'
nz.inputs['Scale'].default_value=float(argv[1]); nz.inputs['Detail'].default_value=7; nz.inputs['Lacunarity'].default_value=2.1
nz.inputs['Gain'].default_value=float(argv[2]); nz.inputs['Offset'].default_value=1.0; nz.inputs['Distortion'].default_value=0.3
L.new(st.outputs[0],nz.inputs['Vector'])
dv=N.new('ShaderNodeMath'); dv.operation='DIVIDE'; dv.inputs[1].default_value=float(argv[3]); L.new(nz.outputs['Fac'],dv.inputs[0])
em=N.new('ShaderNodeEmission'); L.new(dv.outputs[0],em.inputs[0]); o=N.new('ShaderNodeOutputMaterial'); L.new(em.outputs[0],o.inputs[0])
bpy.context.scene.view_settings.view_transform='Standard'
bpy.context.scene.render.filepath=argv[0]; bpy.ops.render.render(write_still=True)
