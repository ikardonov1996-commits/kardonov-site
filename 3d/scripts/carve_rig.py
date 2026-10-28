# Carving animation rig: each stage is shown between two noisy horizontal "chisel fronts".
#   visible  <=>  f_in < z' < f_out      (z' = height + shared noise, same for every stage)
# During transition A->B both use the same front F: A keeps z' < F, B shows z' > F -> exact hand-over.
# Works on a copy of the marble material ("Marble_Carve"), so the asset material stays untouched.
# usage: blender -b anim_carving.blend -P carve_rig.py
import bpy

STAGES = ["Marble_Block", "C1_Pitched", "C3_Relief2", "C4_Freed", "C5_Point", "C6_Claw", "Sculpture_HiRes"]
FPS = 30
HOLD0, TRANS, HOLD, LAST_TRANS, HOLD_END = 20, 38, 8, 56, 40
TOP, BOTTOM = 1.40, -0.20          # front positions beyond the block (z' includes +-0.1 noise)

sc = bpy.context.scene; O = bpy.data.objects
src = bpy.data.materials["Marble"]
src.use_fake_user = True
old = bpy.data.materials.get("Marble_Carve")
if old: bpy.data.materials.remove(old)
mat = src.copy(); mat.name = "Marble_Carve"
nt = mat.node_tree; N = nt.nodes; L = nt.links
out = next(n for n in N if n.type == 'OUTPUT_MATERIAL')
surf = out.inputs['Surface'].links[0].from_socket

def node(t, x, y, **kw):
    n = N.new(t); n.location = (x * 220, y * 220)
    for k, v in kw.items(): setattr(n, k, v)
    return n
def math(op, a, b, x, y):
    n = node('ShaderNodeMath', x, y, operation=op)
    for i, v in enumerate((a, b)):
        if isinstance(v, (int, float)): n.inputs[i].default_value = v
        else: L.new(v, n.inputs[i])
    return n.outputs[0]

tc = node('ShaderNodeTexCoord', 14, 6)                     # object space: all stages share one transform
sep = node('ShaderNodeSeparateXYZ', 15, 6); L.new(tc.outputs['Object'], sep.inputs[0])
n1 = node('ShaderNodeTexNoise', 15, 7); n1.inputs['Scale'].default_value = 5.0; n1.inputs['Detail'].default_value = 3
n2 = node('ShaderNodeTexNoise', 15, 8); n2.inputs['Scale'].default_value = 28.0; n2.inputs['Detail'].default_value = 2
L.new(tc.outputs['Object'], n1.inputs['Vector']); L.new(tc.outputs['Object'], n2.inputs['Vector'])
wob = math('ADD', math('MULTIPLY', math('SUBTRACT', n1.outputs['Fac'], 0.5, 16, 7), 0.16, 16.5, 7),
                  math('MULTIPLY', math('SUBTRACT', n2.outputs['Fac'], 0.5, 16, 8), 0.04, 16.5, 8), 17, 7.5)
zp = math('ADD', sep.outputs['Z'], wob, 17.5, 6.5)          # ragged front, identical for every stage
fin = node('ShaderNodeAttribute', 16, 9, attribute_type='OBJECT', attribute_name='f_in').outputs['Fac']
fout = node('ShaderNodeAttribute', 16, 10, attribute_type='OBJECT', attribute_name='f_out').outputs['Fac']
vis = math('MULTIPLY', math('GREATER_THAN', zp, fin, 18, 8), math('LESS_THAN', zp, fout, 18, 9), 18.5, 8.5)
# inside of a cut shell = cross-section of solid marble: bright fresh stone, never a dark hollow
geo = node('ShaderNodeNewGeometry', 17, 3)
cut_d = node('ShaderNodeBsdfDiffuse', 17, 2); cut_d.inputs['Color'].default_value = (0.93, 0.90, 0.86, 1)
cut_e = node('ShaderNodeEmission', 17, 1); cut_e.inputs['Color'].default_value = (0.93, 0.90, 0.86, 1); cut_e.inputs['Strength'].default_value = 0.45
cut = node('ShaderNodeAddShader', 18, 1.5); L.new(cut_d.outputs[0], cut.inputs[0]); L.new(cut_e.outputs[0], cut.inputs[1])
face = node('ShaderNodeMixShader', 18.8, 3); L.new(geo.outputs['Backfacing'], face.inputs['Fac'])
L.new(surf, face.inputs[1]); L.new(cut.outputs[0], face.inputs[2]); surf = face.outputs[0]
tr = node('ShaderNodeBsdfTransparent', 18.5, 4)
mix = node('ShaderNodeMixShader', 19.5, 5)
L.new(vis, mix.inputs['Fac']); L.new(tr.outputs[0], mix.inputs[1]); L.new(surf, mix.inputs[2])
L.new(mix.outputs[0], out.inputs['Surface'])
mat.surface_render_method = 'DITHERED'
mat.use_transparent_shadow = True            # hidden (already carved) stone must not cast shadows
bsdf = next(n for n in N if n.type == 'BSDF_PRINCIPLED')
bsdf.subsurface_method = 'BURLEY'             # random-walk SSS breaks on the overlapping (hidden) stage shells

# ---- timeline
starts = []; f = 1 + HOLD0
for i in range(len(STAGES) - 1):
    d = LAST_TRANS if i == len(STAGES) - 2 else TRANS
    starts.append((f, f + d)); f += d + HOLD
end = f - HOLD + HOLD_END
sc.frame_start, sc.frame_end = 1, end; sc.render.fps = FPS

def key(ob, prop, frame, val):
    ob[prop] = val; ob.keyframe_insert(data_path='["%s"]' % prop, frame=frame)
for i, name in enumerate(STAGES):
    ob = O[name]; ob.hide_render = False; ob.hide_viewport = False
    ob.data.materials.clear(); ob.data.materials.append(mat)
    if ob.animation_data: ob.animation_data_clear()
    # appear: front sweeps down during transition (i-1 -> i)
    if i == 0: key(ob, "f_in", 1, BOTTOM)
    else:
        a, b = starts[i - 1]; key(ob, "f_in", 1, TOP); key(ob, "f_in", a, TOP); key(ob, "f_in", b, BOTTOM)
    # disappear: same front during transition (i -> i+1)
    if i == len(STAGES) - 1: key(ob, "f_out", 1, TOP)
    else:
        a, b = starts[i]; key(ob, "f_out", 1, TOP); key(ob, "f_out", a, TOP); key(ob, "f_out", b, BOTTOM)
    for fc in ob.animation_data.action.fcurves:
        for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'   # steady chisel pace, exact hand-over
for o in O:
    if o.type == 'MESH' and o.name not in STAGES and o.name != "Floor": o.hide_render = True
key_frames = [1 + HOLD0 // 2] + [b + HOLD // 2 for a, b in starts[:-1]] + [end - HOLD_END // 2]
sc["stage_frames"] = key_frames
print("FRAMES", sc.frame_start, sc.frame_end, "transitions", starts, "stage stills", key_frames)
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath, compress=True)
