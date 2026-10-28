# Marble v7: warm cream stone; veins modelled on real marble (iso-contours of warped fBm).
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

# --- veins: iso-surfaces of domain-warped fBm, drawn with a TRUE distance (|f-level| / |grad f|)
# so width is in metres everywhere (no smeared blobs where the field is flat). Spacing is
# sized to the body (several veins across a forearm or a pec). Hierarchy: main veins,
# sub-parallel secondaries, a weaker crossing family, hairlines only near veins.
EPS = 0.003
def field(Wv, scale, x, y):
    def smp(off, yy):
        v = Wv if off is None else vmath('ADD', Wv, off, x - 1, yy)
        return noise(v, scale, 6, x, yy, rough=0.55)
    f0 = smp(None, y); fx = smp((EPS, 0, 0), y - 0.6); fy = smp((0, EPS, 0), y - 1.2); fz = smp((0, 0, EPS), y - 1.8)
    cx = n('ShaderNodeCombineXYZ', x + 1, y - 1)
    for i, f in enumerate((fx, fy, fz)): L.new(math('SUBTRACT', f, f0, x + 0.6, y - 0.6 * (i + 1)), cx.inputs[i])
    ln = n('ShaderNodeVectorMath', x + 1.5, y - 1, operation='LENGTH'); L.new(cx.outputs[0], ln.inputs[0])
    g = math('MAXIMUM', math('DIVIDE', ln.outputs['Value'], EPS, x + 2, y - 1), 0.5, x + 2.5, y - 1)   # |grad f| per metre
    return f0, g
def dist(f, g, level, x, y):            # metres to the iso-surface f == level
    return math('DIVIDE', math('ABSOLUTE', math('SUBTRACT', f, level, x, y), None, x + 0.3, y), g, x + 0.6, y)
def dist_k(f, g, k, x, y):              # metres to the nearest of k evenly spaced levels
    fr = math('FRACT', math('ADD', math('MULTIPLY', f, k, x, y), 0.5, x + 0.2, y), None, x + 0.4, y)
    return math('DIVIDE', math('DIVIDE', math('ABSOLUTE', math('SUBTRACT', fr, 0.5, x + 0.6, y), None, x + 0.8, y), k, x + 1, y), g, x + 1.2, y)
def stroke(d, wmin, wmax, taper, x, y):  # 1 inside the vein, width tapers (and breaks) along it
    w = math('ADD', wmin, math('MULTIPLY', taper, wmax - wmin, x, y), x + 0.3, y)
    r = n('ShaderNodeMapRange', x + 0.6, y, interpolation_type='SMOOTHSTEP'); r.inputs['From Min'].default_value = 0.0
    L.new(w, r.inputs['From Max']); L.new(d, r.inputs['Value'])
    return math('SUBTRACT', 1.0, r.outputs['Result'], x + 1, y)
def taper_of(Wv, scale, lo, hi, x, y): return smoothstep(noise(Wv, scale, 3, x, y), lo, hi, x + 1, y)

Wa = warp(warp(vmath('MULTIPLY', P, (1.0, 0.45, 1.0), -11, 12), 1.5, 0.30, -10, 12), 5.0, 0.05, -10, 14)
Wb = warp(warp(vmath('ADD', vmath('MULTIPLY', P, (0.45, 1.0, 1.0), -11, 20), (7.3, 1.1, 3.9), -11, 21), 1.6, 0.28, -10, 20), 5.0, 0.05, -10, 22)
fA, gA = field(Wa, 4.5, -8, 12)
fB, gB = field(Wb, 6.0, -8, 20)
dA = dist(fA, gA, 0.5, -5, 12); dA2 = dist_k(fA, gA, 6, -5, 11)
dB = dist(fB, gB, 0.5, -5, 20); dB2 = dist_k(fB, gB, 5, -5, 19)
tA = taper_of(Wa, 6.0, 0.35, 0.65, -5, 13); tA2 = taper_of(Wa, 9.0, 0.45, 0.70, -5, 14)
tB = taper_of(Wb, 7.0, 0.40, 0.68, -5, 21); tB2 = taper_of(Wb, 11.0, 0.50, 0.72, -5, 22)
mainA = stroke(dA, 0.0004, 0.0026, tA, -3, 12)
secA = stroke(dA2, 0.0002, 0.0010, tA2, -3, 11)
mainB = stroke(dB, 0.0003, 0.0016, tB, -3, 20)
secB = stroke(dB2, 0.00015, 0.0007, tB2, -3, 19)
# hairlines: fine field, only within ~2 cm of a vein
fH, gH = field(warp(Wa, 12.0, 0.01, -8, 26), 14.0, -6, 26)
nearV = math('SUBTRACT', 1.0, smoothstep(math('MINIMUM', dA, dB, -3, 25), 0.0, 0.02, -2.5, 25), -2, 25)
hair = math('MULTIPLY', stroke(dist(fH, gH, 0.5, -3, 26), 0.00012, 0.00035, 1.0, -2, 26), math('MULTIPLY', nearV, 0.5, -1.5, 25), -1, 26)
core = math('MAXIMUM', math('MAXIMUM', math('MAXIMUM', mainA, math('MULTIPLY', secA, 0.75, 0, 11), 0.5, 12),
            math('MAXIMUM', math('MULTIPLY', mainB, 0.65, 0, 20), math('MULTIPLY', secB, 0.45, 0, 19), 0.5, 20), 1, 16), hair, 1.5, 16)
# narrow bleed of colour right beside the veins (no free-floating patches)
glowA = math('MULTIPLY', math('SUBTRACT', 1.0, smoothstep(dA, 0.0, 0.006, -3, 15), -2.5, 15), tA, -2, 15)
glowS = math('MULTIPLY', math('SUBTRACT', 1.0, smoothstep(dA2, 0.0, 0.003, -3, 16), -2.5, 16), tA2, -2, 16)
halo = math('MAXIMUM', glowA, math('MULTIPLY', glowS, 0.5, -1.5, 16), -1, 15)
thick = math('MULTIPLY', mainA, tA, 0, 13)    # dark centre only where the main vein is thick

VEIN = (0.973, 0.597, 0.231)   # #FCCB84 (sRGB) in linear
# --- body: warm ivory with soft cloudy patches
cl = noise(W1, 2.6, 8, -3, -3, rough=0.6)
body = ramp(cl, [(0.28, (0.86, 0.72, 0.64)), (0.52, (0.94, 0.85, 0.79)), (0.80, (0.97, 0.92, 0.88))], -1, -3, 'Body')
# faint ochre bleed hugging the veins (muted, not skin-toned)
body = mix(math('MULTIPLY', halo, 0.35, 2.5, -5), body, (0.95, 0.75, 0.52), 2.8, -3)
col = mix(math('MULTIPLY', halo, 0.25, 2, 1), body, VEIN, 3, 0)
vein_col = ramp(thick, [(0.0, VEIN), (0.85, VEIN), (1.0, (0.88, 0.52, 0.19))], 3, -1.5, 'Vein colour')   # thick veins get a slightly deeper centre
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
