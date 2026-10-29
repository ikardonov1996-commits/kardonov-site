import bpy, os
mode=os.environ.get("WMODE","cur")
W=bpy.context.scene.world; N,L=W.node_tree.nodes,W.node_tree.links
mix=[n for n in N if n.type=='MIX_SHADER'][0]; lp=[n for n in N if n.type=='LIGHT_PATH'][0]
if mode=="glossy":
    # fac = camera OR not glossy -> dark ; env only for glossy
    mt=N.new("ShaderNodeMath"); mt.operation='SUBTRACT'; mt.inputs[0].default_value=1.0
    L.new(lp.outputs["Is Glossy Ray"], mt.inputs[1])
    mx=N.new("ShaderNodeMath"); mx.operation='MAXIMUM'
    L.new(lp.outputs["Is Camera Ray"], mx.inputs[0]); L.new(mt.outputs[0], mx.inputs[1])
    L.new(mx.outputs[0], mix.inputs[0])
if mode=="dark":
    L.new(lp.outputs["Is Camera Ray"], mix.inputs[0]); mix.inputs[0].default_value=1
    for l in list(L):
        if l.to_node==mix and l.to_socket==mix.inputs[0]: L.remove(l)
    mix.inputs[0].default_value=1.0
print("WMODE",mode)
