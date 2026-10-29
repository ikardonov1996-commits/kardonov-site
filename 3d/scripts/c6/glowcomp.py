# Compositor (v5): Fog Glow halo computed ONLY from emission data, added on top of the image (marble never blooms).
#  1) blue/amber neon: glare of the Emit pass (as v4)
#  2) headband: extra soft amber halo from the shader AOV "amber_glow" (written only by the headband glow materials)
import bpy
AOV = "amber_glow"
def setup_glow(sc, gain=1.0, thr=0.4, size=9, amber_gain=4.5, amber_size=9):
    for vl in sc.view_layers:
        vl.use_pass_emit = True
        if AOV not in [a.name for a in vl.aovs]:
            a = vl.aovs.add(); a.name = AOV; a.type = 'COLOR'
    sc.use_nodes = True; nt = sc.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    rl = nt.nodes.new('CompositorNodeRLayers'); comp = nt.nodes.new('CompositorNodeComposite')
    g = nt.nodes.new('CompositorNodeGlare'); g.glare_type = 'FOG_GLOW'; g.quality = 'HIGH'; g.threshold = thr; g.size = size; g.mix = 1.0
    mx = nt.nodes.new('CompositorNodeMixRGB'); mx.blend_type = 'ADD'; mx.inputs[0].default_value = gain
    nt.links.new(rl.outputs['Emit'], g.inputs['Image'])
    nt.links.new(rl.outputs['Image'], mx.inputs[1]); nt.links.new(g.outputs['Image'], mx.inputs[2])
    out = mx
    if AOV in rl.outputs:
        ga = nt.nodes.new('CompositorNodeGlare'); ga.glare_type = 'FOG_GLOW'; ga.quality = 'HIGH'; ga.threshold = 0.0; ga.size = amber_size; ga.mix = 1.0
        ma = nt.nodes.new('CompositorNodeMixRGB'); ma.blend_type = 'ADD'; ma.inputs[0].default_value = amber_gain
        nt.links.new(rl.outputs[AOV], ga.inputs['Image'])
        nt.links.new(mx.outputs['Image'], ma.inputs[1]); nt.links.new(ga.outputs['Image'], ma.inputs[2])
        out = ma
    nt.links.new(out.outputs['Image'], comp.inputs['Image'])
    try:
        v = nt.nodes.new('CompositorNodeViewer'); nt.links.new(out.outputs['Image'], v.inputs['Image'])
    except Exception: pass

def add_aov(m, color, strength):
    """write `color*strength` to the amber_glow AOV from material m (surface shading unchanged)"""
    N, L = m.node_tree.nodes, m.node_tree.links
    for n in list(N):
        if n.type == 'OUTPUT_AOV': N.remove(n)
    o = N.new('ShaderNodeOutputAOV'); o.aov_name = AOV
    o.inputs['Color'].default_value = (color[0] * strength, color[1] * strength, color[2] * strength, 1)
