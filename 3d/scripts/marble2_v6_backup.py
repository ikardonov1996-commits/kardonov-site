# Marble v6: warm cream stone; veins modelled on real marble (iso-contours of warped fBm).
# The texture lives in the space of empty "MarbleSpace", so the raw block and the
# sculpture show the same veins when carved. Object props: "polish" (0 raw .. 1 honed),
# "gold" (1 = metallic gold veins).
# usage: blender -b IN.blend -P marble2.py -- OUT.blend
import bpy, sys
argv = sys.argv[sys.argv.index("--") + 1:]
out_path = argv[0]
space = bpy.data.objects["MarbleSpace"]

m = bpy.data.materials.get("Marble") or bpy.data.materials.new("Marble")
m.use_nodes = True; nt = m.node_tree; N = nt.nodes; L = nt.links; N.clear()

def n(t, x, y, **kw):
    node = N.new(t); node.location = (x * 220, y * 220)
    for k, v in kw.items(): setattr(node, k, v)
    return node
def link(a, b):
    if isinstance(a, (int, float)): b.default_value = a
    else: L.new(a, b)
def math(op, a, b=None, x=0, y=0):
    node = n('ShaderNodeMath', x, y, operation=op)
    for i, v in enumerate((a, b)):
        if v is not None: link(v, node.inputs[i])
    return node.outputs[0]
def vmath(op, a, b, x, y):
    node = n('ShaderNodeVectorMath', x, y, operation=op)
    L.new(a, node.inputs[0])
    if op == 'SCALE': node.inputs['Scale'].default_value = b
    elif isinstance(b, tuple): node.inputs[1].default_value = b
    else: L.new(b, node.inputs[1])
    return node.outputs[0]
def noise(vec, scale, detail, x, y, rough=0.5, out='Fac'):
    t = n('ShaderNodeTexNoise', x, y); t.inputs['Scale'].default_value = scale
    t.inputs['Detail'].default_value = detail; t.inputs['Roughness'].default_value = rough
    L.new(vec, t.inputs['Vector']); return t.outputs[out]
def smoothstep(v, lo, hi, x, y):
    r = n('ShaderNodeMapRange', x, y, interpolation_type='SMOOTHSTEP')
    r.inputs['From Min'].default_value = lo; r.inputs['From Max'].default_value = hi
    link(v, r.inputs['Value']); return r.outputs['Result']
def maprange(v, lo, hi, a, b, x, y):
    r = n('ShaderNodeMapRange', x, y)
    for k, val in (('From Min', lo), ('From Max', hi), ('To Min', a), ('To Max', b)): r.inputs[k].default_value = val
    link(v, r.inputs['Value']); return r.outputs['Result']
def ramp(src, stops, x, y, label=''):
    r = n('ShaderNodeValToRGB', x, y); r.label = label; e = r.color_ramp.elements
    while len(e) < len(stops): e.new(0)
    for el, (p, c) in zip(e, stops): el.position = p; el.color = (*c, 1)
    L.new(src, r.inputs['Fac']); return r.outputs['Color']
def rgba(sockets, name): return next(s for s in sockets if s.name == name and s.type == 'RGBA')
def mix(fac, a, b, x, y, blend='MIX'):
    node = n('ShaderNodeMix', x, y, data_type='RGBA', blend_type=blend)
    link(fac, next(s for s in node.inputs if s.name == 'Factor' and s.type == 'VALUE'))
    for name, v in (('A', a), ('B', b)):
        if isinstance(v, tuple): rgba(node.inputs, name).default_value = (*v, 1)
        else: L.new(v, rgba(node.inputs, name))
    return rgba(node.outputs, 'Result')

out = n('ShaderNodeOutputMaterial', 16, 0)
bsdf = n('ShaderNodeBsdfPrincipled', 14, 0); L.new(bsdf.outputs[0], out.inputs['Surface'])
tc = n('ShaderNodeTexCoord', -12, 0); tc.object = space
polish = n('ShaderNodeAttribute', -12, -8, attribute_type='OBJECT', attribute_name='polish').outputs['Fac']
gold = n('ShaderNodeAttribute', -12, -9, attribute_type='OBJECT', attribute_name='gold').outputs['Fac']
P = tc.outputs['Object']

# --- coordinates: stretch along one axis so veins flow in a direction, then domain-warp
Pf = vmath('MULTIPLY', P, (1.0, 0.5, 1.0), -11, 2)
def warp(vec, scale, amount, x, y):
    c = noise(vec, scale, 4, x, y, out='Color')
    return vmath('ADD', vec, vmath('SCALE', vmath('SUBTRACT', c, (0.5, 0.5, 0.5), x + 1, y), amount, x + 1.5, y), x + 2, y)
W1 = warp(Pf, 1.6, 0.28, -10, 4)
W2 = warp(W1, 6.0, 0.06, -10, 6)
W = warp(W2, 24.0, 0.012, -10, 8)

# --- veins: iso-contours of strongly domain-warped fBm (real marble: long jagged veins in
# a flow direction, braided strands along the main veins, a weaker crossing family,
# hairlines only inside vein corridors, large clean fields in between)
def ss_s(v, lo, hi, x, y):   # smoothstep with socket-or-float upper bound
    r = n('ShaderNodeMapRange', x, y, interpolation_type='SMOOTHSTEP'); r.inputs['From Min'].default_value = lo
    link(hi, r.inputs['From Max']); link(v, r.inputs['Value']); return r.outputs['Result']
def line(f, level, w, x, y):   # 1 on the iso-contour f == level, half-width w (noise units)
    return math('SUBTRACT', 1.0, ss_s(math('ABSOLUTE', math('SUBTRACT', f, level, x, y), None, x + 0.3, y), 0.0, w, x + 0.6, y), x + 1, y)
def family(Wv, scale, x, y):
    f = noise(Wv, scale, 7, x, y, rough=0.58)
    w = math('ADD', 0.0015, math('MULTIPLY', smoothstep(noise(Wv, 4.0, 3, x, y - 1), 0.3, 0.7, x + 1, y - 1), 0.008, x + 2, y - 1), x + 3, y - 1)
    main = line(f, 0.5, w, x + 1, y)
    sec = math('MAXIMUM', line(f, 0.41, math('MULTIPLY', w, 0.7, x + 2, y - 2), x + 3, y - 2),
               line(f, 0.59, math('MULTIPLY', w, 0.7, x + 2, y - 2.5), x + 3, y - 2.5), x + 4, y - 2)
    near = line(f, 0.5, 0.06, x + 1, y - 3)
    sw = math('MULTIPLY', w, 0.4, x + 2, y - 3.5)
    strands = math('MULTIPLY', math('MAXIMUM', line(f, 0.462, sw, x + 3, y - 3.5), line(f, 0.538, sw, x + 3, y - 4), x + 4, y - 3.5), near, x + 5, y - 3.5)
    glow = line(f, 0.5, math('MULTIPLY', w, 5.0, x + 2, y - 4.5), x + 3, y - 4.5)        # soft bleed beside the vein
    return main, sec, strands, near, glow
Wa = warp(warp(vmath('MULTIPLY', P, (1.0, 0.35, 1.0), -11, 12), 1.2, 0.45, -10, 12), 3.5, 0.12, -10, 14)
Wb = warp(warp(vmath('ADD', vmath('MULTIPLY', P, (0.35, 1.0, 1.0), -11, 20), (7.3, 1.1, 3.9), -11, 21), 1.3, 0.40, -10, 20), 3.5, 0.10, -10, 22)
mA, sA, stA, nearA, glA = family(Wa, 1.8, -7, 12)
mB, sB, stB, nearB, glB = family(Wb, 2.3, -7, 20)
hf = noise(warp(Wa, 9.0, 0.03, -7, 26), 9.0, 7, -5, 26, rough=0.58)
hair = math('MULTIPLY', line(hf, 0.5, 0.007, -4, 26), math('MULTIPLY', math('MAXIMUM', nearA, nearB, -4, 25), 0.55, -3, 25), -2, 26)
famA = math('MAXIMUM', math('MAXIMUM', mA, math('MULTIPLY', sA, 0.75, 0, 12), 0.5, 12), math('MULTIPLY', stA, 0.8, 0, 11), 1, 12)
famB = math('MAXIMUM', math('MAXIMUM', mB, math('MULTIPLY', sB, 0.75, 0, 20), 0.5, 20), math('MULTIPLY', stB, 0.8, 0, 19), 1, 20)
core = math('MAXIMUM', math('MAXIMUM', famA, math('MULTIPLY', famB, 0.6, 1.5, 19), 2, 16), hair, 2.5, 16)
halo = math('MAXIMUM', glA, math('MULTIPLY', glB, 0.6, 1.5, 18), 2, 18)
cluster = math('MAXIMUM', nearA, math('MULTIPLY', nearB, 0.6, 1.5, 17), 2, 17)   # vein corridors (used by the fog)
thick = mA   # only main veins of the primary family get the dark centre

# --- body: warm ivory with soft cloudy patches
cl = noise(W1, 2.6, 8, -3, -3, rough=0.6)
body = ramp(cl, [(0.28, (0.86, 0.72, 0.64)), (0.52, (0.94, 0.85, 0.79)), (0.80, (0.97, 0.92, 0.88))], -1, -3, 'Body')
# orange fog: soft cloudy haze that gathers around veins and in vein clusters
fogn = smoothstep(noise(W1, 3.2, 6, 0, -5, rough=0.6), 0.36, 0.68, 1, -5)
fog = math('MULTIPLY', math('ADD', math('MULTIPLY', fogn, cluster, 1.5, -5), math('MULTIPLY', halo, 1.0, 1.5, -5.5), 2, -5), 1.8, 2.5, -5)
body = mix(math('MINIMUM', fog, 0.7, 2.8, -5), body, (0.91, 0.64, 0.44), 2.8, -3)
col = mix(math('MULTIPLY', halo, 0.75, 2, 1), body, (0.90, 0.62, 0.40), 3, 0)
vein_col = ramp(thick, [(0.0, (0.84, 0.50, 0.24)), (0.6, (0.74, 0.38, 0.14)), (1.0, (0.52, 0.24, 0.08))], 3, -1.5, 'Vein colour')
col = mix(core, col, vein_col, 4, 0)
col = mix(math('MULTIPLY', core, gold, 4.5, -2.5), col, (1.0, 0.70, 0.30), 5, 0)          # optional gold veins
col = mix(math('MULTIPLY', math('SUBTRACT', 1.0, polish, 5, -3), 0.3, 5.5, -3), col, (0.90, 0.86, 0.82), 6, 0)  # raw = dusty
xt = n('ShaderNodeTexVoronoi', 6, 2); xt.inputs['Scale'].default_value = 900; L.new(P, xt.inputs['Vector'])
crystals = maprange(xt.outputs['Distance'], 0, 1, 0.95, 1.03, 7, 2)        # fine crystalline mottling
col = mix(1.0, col, (1, 1, 1), 7.5, 0, blend='MULTIPLY')
L.new(crystals, rgba(col.node.inputs, 'B'))
L.new(col, bsdf.inputs['Base Color'])
L.new(math('MULTIPLY', core, gold, 12, -1), bsdf.inputs['Metallic'])

# --- honed finish
rough = maprange(polish, 0, 1, 0.75, 0.46, 11, -3)
rv = noise(P, 25, 2, 11, -4.5)
rr = math('ADD', rough, math('MULTIPLY', math('SUBTRACT', rv, 0.5, 11.5, -4.5), 0.25, 12, -4.5), 12.5, -3.5)
L.new(math('ADD', rr, math('MULTIPLY', core, 0.10, 12.5, -4.8), 13, -3.5), bsdf.inputs['Roughness'])
bsdf.inputs['Subsurface Weight'].default_value = 0.6
bsdf.inputs['Subsurface Radius'].default_value = (1.0, 0.72, 0.5)
bsdf.inputs['Subsurface Scale'].default_value = 0.006
bsdf.inputs['Coat Weight'].default_value = 0.0
bsdf.inputs['Specular IOR Level'].default_value = 0.4

# --- chisel grain + slightly recessed veins; strong when raw
grain = noise(P, 160, 4, 10, -6)
chips = n('ShaderNodeTexVoronoi', 10, -8); chips.inputs['Scale'].default_value = 45; L.new(P, chips.inputs['Vector'])
height = math('SUBTRACT', math('ADD', grain, chips.outputs['Distance'], 11, -7), math('MULTIPLY', core, 0.3, 11, -8), 11.5, -7)
bstr = maprange(polish, 0, 1, 0.4, 0.03, 11, -9)
bump = n('ShaderNodeBump', 13, -7); bump.inputs['Distance'].default_value = 0.002
L.new(bstr, bump.inputs['Strength']); L.new(height, bump.inputs['Height']); L.new(bump.outputs['Normal'], bsdf.inputs['Normal'])

bpy.ops.wm.save_as_mainfile(filepath=out_path, compress=True)
print("MARBLE v4 OK")
