# Compositor: Fog Glow halo computed ONLY from the emission pass, added on top of the image (marble never blooms).
def setup_glow(sc, gain=1.0, thr=0.4, size=9):
    for vl in sc.view_layers: vl.use_pass_emit = True
    sc.use_nodes = True; nt = sc.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    rl = nt.nodes.new('CompositorNodeRLayers'); comp = nt.nodes.new('CompositorNodeComposite')
    g = nt.nodes.new('CompositorNodeGlare'); g.glare_type = 'FOG_GLOW'; g.quality = 'HIGH'; g.threshold = thr; g.size = size; g.mix = 1.0
    mx = nt.nodes.new('CompositorNodeMixRGB'); mx.blend_type = 'ADD'; mx.inputs[0].default_value = gain
    nt.links.new(rl.outputs['Emit'], g.inputs['Image'])
    nt.links.new(rl.outputs['Image'], mx.inputs[1]); nt.links.new(g.outputs['Image'], mx.inputs[2])
    nt.links.new(mx.outputs['Image'], comp.inputs['Image'])
    try:
        v = nt.nodes.new('CompositorNodeViewer'); nt.links.new(mx.outputs['Image'], v.inputs['Image'])
    except Exception: pass
