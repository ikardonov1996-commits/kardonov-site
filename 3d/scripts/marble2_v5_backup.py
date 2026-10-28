# Marble v4: warm cream stone with an organic, clustered network of orange veins.
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

# --- where veins gather: low-frequency cluster mask (0 = clean stone, 1 = dense veining)
cluster = smoothstep(noise(P, 1.1, 2, -7, 10), 0.40, 0.66, -6, 10)
cluster = maprange(cluster, 0, 1, 0.6, 1.0, -5, 10)

def veins(scale, wmin, wmax, x, y):
    """Voronoi crack network. Width tapers smoothly along the vein (never a hard stop)."""
    v = n('ShaderNodeTexVoronoi', x, y, feature='DISTANCE_TO_EDGE')
    v.inputs['Scale'].default_value = scale; v.inputs['Randomness'].default_value = 1.0
    L.new(W, v.inputs['Vector'])
    taper = smoothstep(noise(W, scale * 0.7, 2, x, y - 1), 0.30, 0.70, x + 1, y - 1)
    w = math('MULTIPLY', maprange(taper, 0, 1, wmin, wmax, x + 2, y - 1), cluster, x + 3, y - 1)
    q = math('DIVIDE', v.outputs['Distance'], math('MAXIMUM', w, 1e-5, x + 3.5, y - 1), x + 4, y)
    core = math('POWER', math('SUBTRACT', 1.0, math('MINIMUM', q, 1.0, x + 4.5, y), x + 5, y), 1.5, x + 5.5, y)
    halo = math('POWER', math('SUBTRACT', 1.0, math('MINIMUM', math('MULTIPLY', q, 0.08, x + 4.5, y - 0.5), 1.0, x + 4.8, y - 0.5), x + 5, y - 0.5), 3.0, x + 5.5, y - 0.5)
    return core, halo

# thick primary veins, thinner secondaries; widths small vs. cell size -> no filled blobs
c1, h1 = veins(8.5, 0.0040, 0.020, -6, 6)
c2, h2 = veins(22.0, 0.0012, 0.0055, -6, 3)
# hairlines: iso-contour of warped noise -> thin wandering lines, never closed fills
hl = noise(W2, 7.0, 6, -6, 0, rough=0.55)
hair = math('MULTIPLY', math('SUBTRACT', 1.0, smoothstep(math('ABSOLUTE', math('SUBTRACT', hl, 0.5, -5, 0), None, -4.5, 0), 0.0, 0.006, -4, 0), -3.5, 0), cluster, -3, 0)

core = math('MAXIMUM', math('MAXIMUM', c1, math('MULTIPLY', c2, 0.9, 0, 3), 0.5, 4), math('MULTIPLY', hair, 0.6, 0, 0), 1, 4)
halo = math('MAXIMUM', h1, math('MULTIPLY', h2, 0.6, 0, 2), 1, 2)
thick = c1   # only primary veins get the dark centre

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
