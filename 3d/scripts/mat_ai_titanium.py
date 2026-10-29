# Shared "AI" metal v3: light cool satin titanium with a refined machined-surface texture.
# One material for robo-arm plating, chisel body and windlass crank lever.
# v1 (roughness 0.34, base 0.62) read dark on the site (#0f0f12); v2 = light, diffuse, but too uniform.
# v3 keeps v2's average colour / brightness / roughness and adds (colour/roughness only, NO bump):
#   * fine directional brushed grain (lines ~1-2 mm wide, run along the part's grain axis), colour +-5 %
#   * wider soft brushing streaks (~1-2 cm) along the same axis, colour +-5 %, roughness +-0.05
#   * soft large-scale cloudy tonal variation, +-4 %
#   * very faint, patchy machining rings across the grain axis (~11 mm pitch, up to -3.5 % / +0.04 roughness)
# Coordinates: Object space (metres), so the pattern sticks to the part and has a physical size.
# Grain axis = object custom property "ti_grain_dir" (3 floats, object-local), default local Z when absent.
#   e.g.  obj["ti_grain_dir"] = (1.0, 0.0, 0.0)
# ai_titanium() always rebuilds all nodes/params, so calling it upgrades v1/v2 files in place.
# usage inside Blender:  import sys; sys.path.append(SCRIPTS); from mat_ai_titanium import ai_titanium; m = ai_titanium()
import bpy, math

BASE = (0.78, 0.81, 0.85)          # ~#E4E7EB sRGB: very light, cool (same as v2)

def ai_titanium(name="AI_Titanium"):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True; m.use_fake_user = True
    N, L = m.node_tree.nodes, m.node_tree.links
    for n in [n for n in N if n.type not in ('BSDF_PRINCIPLED', 'OUTPUT_MATERIAL')]: N.remove(n)
    b = next(n for n in N if n.type == 'BSDF_PRINCIPLED')
    out = next(n for n in N if n.type == 'OUTPUT_MATERIAL')
    if not out.inputs["Surface"].links: L.new(b.outputs["BSDF"], out.inputs["Surface"])
    b.location = (900, 0); out.location = (1200, 0)
    b.inputs["Metallic"].default_value = 0.85                        # a little diffuse so it keeps value without a bright env
    b.inputs["Coat Weight"].default_value = 0.0
    b.inputs["Normal"].default_value = (0, 0, 0)
    for s in ("Normal", "Tangent"):
        for l in list(b.inputs[s].links): L.remove(l)

    def node(t, x, y, **kw):
        n = N.new(t); n.location = (x, y)
        for k, v in kw.items(): setattr(n, k, v)
        return n
    def vm(op, a, b_=None, x=0, y=0, scale=None):
        n = node("ShaderNodeVectorMath", x, y, operation=op)
        L.new(a, n.inputs[0])
        if b_ is not None:
            if isinstance(b_, tuple): n.inputs[1].default_value = b_
            else: L.new(b_, n.inputs[1])
        if scale is not None: n.inputs[3].default_value = scale
        return n
    def math(op, a, b_=None, x=0, y=0, clamp=False):
        n = node("ShaderNodeMath", x, y, operation=op, use_clamp=clamp)
        for i, v in enumerate((a, b_)):
            if v is None: continue
            if isinstance(v, (int, float)): n.inputs[i].default_value = v
            else: L.new(v, n.inputs[i])
        return n
    def noise(vec, scale, detail, rough, x, y):
        n = node("ShaderNodeTexNoise", x, y); n.noise_dimensions = '3D'
        n.inputs["Scale"].default_value = scale; n.inputs["Detail"].default_value = detail
        n.inputs["Roughness"].default_value = rough
        L.new(vec, n.inputs["Vector"]); return n
    def signed(sock, lo, hi, x, y):                 # noise fac [lo,hi] -> [-1,1] clamped
        n = node("ShaderNodeMapRange", x, y); n.clamp = True
        n.inputs[1].default_value = lo; n.inputs[2].default_value = hi
        n.inputs[3].default_value = -1.0; n.inputs[4].default_value = 1.0
        L.new(sock, n.inputs[0]); return n

    tc = node("ShaderNodeTexCoord", -1400, 0)
    at = node("ShaderNodeAttribute", -1400, -300, attribute_type='OBJECT', attribute_name="ti_grain_dir")
    d0 = vm('ADD', at.outputs["Vector"], (0.0, 0.0, 1e-4), -1200, -300)
    dr = vm('NORMALIZE', d0.outputs[0], None, -1050, -300)
    p = tc.outputs["Object"]
    along = vm('DOT_PRODUCT', p, dr.outputs[0], -900, -200)                  # coordinate along the grain
    ax = vm('SCALE', dr.outputs[0], None, -750, -300); L.new(along.outputs["Value"], ax.inputs["Scale"])
    ax2 = vm('SCALE', ax.outputs[0], None, -600, -300, scale=0.985)
    perp = vm('SUBTRACT', p, ax2.outputs[0], -450, -150)                       # grain lines: ~65x stretched along axis

    g_fine = noise(perp.outputs[0], 650.0, 3.0, 0.55, -250, 200)              # brushed lines ~1-2 mm
    g_str = noise(perp.outputs[0], 55.0, 2.0, 0.5, -250, -50)                 # wider brushing streaks (~1-2 cm)
    cloud = noise(p, 7.0, 2.0, 0.45, -250, -300)                              # soft large-scale tone
    gf = signed(g_fine.outputs["Fac"], 0.36, 0.64, -50, 200)
    gs = signed(g_str.outputs["Fac"], 0.38, 0.62, -50, -50)
    cl = signed(cloud.outputs["Fac"], 0.38, 0.62, -50, -300)
    # machining rings across the grain axis, slightly wobbly, thin: pow(0.5+0.5 sin, 14)
    wob = math('MULTIPLY', cloud.outputs["Fac"], 1.6, -250, -550)
    ph = math('MULTIPLY', along.outputs["Value"], 2 * 3.14159265 / 0.011, -450, -500)
    ph2 = math('ADD', ph.outputs[0], wob.outputs[0], -50, -500)
    sn = math('SINE', ph2.outputs[0], None, 100, -500)
    s01 = math('MULTIPLY_ADD', sn.outputs[0], 0.5, 250, -500); s01.inputs[2].default_value = 0.5
    rings = math('POWER', s01.outputs[0], 14.0, 400, -500)
    # rings fade in/out along and around the part (irregular, never a regular ladder)
    rn = noise(p, 22.0, 1.0, 0.5, 250, -700)
    rm = node('ShaderNodeMapRange', 400, -700); rm.clamp = True
    rm.inputs[1].default_value = 0.52; rm.inputs[2].default_value = 0.68; L.new(rn.outputs['Fac'], rm.inputs[0])
    rgate = math('MULTIPLY', rings.outputs[0], rm.outputs[0], 550, -550)

    # colour factor = 1 + 0.03*fine + 0.02*streak + 0.03*cloud - 0.02*rings (+0.004 mean comp)
    def acc(prev, sock, k, x, y):
        n = math('MULTIPLY_ADD', sock, k, x, y); L.new(prev, n.inputs[2]); return n.outputs[0]
    v = math('MULTIPLY_ADD', gf.outputs[0], 0.05, 150, 200); v.inputs[2].default_value = 1.004
    v = acc(v.outputs[0], gs.outputs[0], 0.05, 300, 150)
    v = acc(v, cl.outputs[0], 0.04, 450, 100)
    v = acc(v, rgate.outputs[0], -0.035, 600, 50)
    rgb = node("ShaderNodeRGB", 450, 400); rgb.outputs[0].default_value = (*BASE, 1)
    col = node("ShaderNodeVectorMath", 700, 300, operation='SCALE')
    L.new(rgb.outputs[0], col.inputs[0]); L.new(v, col.inputs["Scale"])
    L.new(col.outputs[0], b.inputs["Base Color"])
    # roughness: v2 mean ~0.49; brighter brushed lines slightly smoother, rings slightly rougher
    r = math('MULTIPLY_ADD', gf.outputs[0], -0.03, 300, -150); r.inputs[2].default_value = 0.485
    r = acc(r.outputs[0], gs.outputs[0], -0.05, 450, -200)
    r = acc(r, cl.outputs[0], 0.02, 600, -250)
    r = acc(r, rgate.outputs[0], 0.04, 750, -300)
    L.new(r, b.inputs["Roughness"])
    # anisotropy, modulated by the streaks (EEVEE Next ignores it; harmless in Cycles)
    an = math('MULTIPLY_ADD', gs.outputs[0], 0.06, 600, -400); an.inputs[2].default_value = 0.2
    L.new(an.outputs[0], b.inputs["Anisotropic"])
    b.inputs["Anisotropic Rotation"].default_value = 0.0
    return m
