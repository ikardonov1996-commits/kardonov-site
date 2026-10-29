# EEVEE renders of asset_tools.blend (file is NOT saved by this script)
# args after --: out_prefix  view1,view2,...|all  [res=800] [samples=16] [force=0] [glare=1]
import bpy, sys, math, os
from mathutils import Vector as V, Matrix

argv = sys.argv[sys.argv.index("--") + 1:]
PRE = argv[0]; want = argv[1]
RES = int(argv[2]) if len(argv) > 2 else 800
SAMP = int(argv[3]) if len(argv) > 3 else 16
FORCE = len(argv) > 4 and argv[4] == "1"
GLARE = not (len(argv) > 5 and argv[5] == "0")
D = bpy.data; sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE_NEXT'; sc.eevee.taa_render_samples = SAMP
sc.render.resolution_x = sc.render.resolution_y = RES; sc.render.resolution_percentage = 100
sc.render.film_transparent = True
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'
try:
    sc.eevee.use_raytracing = True; sc.eevee.ray_tracing_options.resolution_scale = '2'
    sc.eevee.use_shadows = True
except Exception as e: print("rt", e)
if GLARE:
    sc.use_nodes = True; nt = sc.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    rl = nt.nodes.new('CompositorNodeRLayers'); comp = nt.nodes.new('CompositorNodeComposite')
    g = nt.nodes.new('CompositorNodeGlare'); g.glare_type = 'FOG_GLOW'; g.quality = 'HIGH'; g.threshold = 1.6; g.size = 6; g.mix = -0.55
    nt.links.new(rl.outputs['Image'], g.inputs['Image']); nt.links.new(g.outputs['Image'], comp.inputs['Image'])

HAM, CHI, CAM = D.objects["Hammer"], D.objects["Chisel"], sc.camera
CENTER = V((0, 0, 0.16))

def kids(e): return [o for o in e.children_recursive if o.type == 'MESH']
def place(e, center=CENTER, rot=(0, 0, 0)):
    e.rotation_euler = rot; e.location = (0, 0, 0); bpy.context.view_layer.update()
    pts = [o.matrix_world @ V(c) for o in kids(e) for c in o.bound_box]
    mn = V((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    mx = V((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    e.location = center - (mn + mx) / 2; bpy.context.view_layer.update()
def show(*es):
    for e in (HAM, CHI):
        vis = e in es
        for o in [e] + list(e.children_recursive): o.hide_render = not vis

def shoot(name, direction, target=None, size=None, objs=None, lens=85, up=V((0, 0, 1))):
    path = f"{PRE}_{name}.png"
    if os.path.exists(path) and not FORCE: print("SKIP", name); return
    d = V(direction).normalized(); target = V(target) if target else None
    CAM.data.lens = lens; CAM.data.type = 'PERSP'; CAM.data.clip_start = 0.005
    rot = (-d).to_track_quat('-Z', 'Y')
    if target is None or size is None:
        pts = [o.matrix_world @ V(c) for o in objs for c in o.bound_box]
        if target is None: target = sum(pts, V()) / len(pts)
        R = rot.to_matrix(); right, upv = R.col[0], R.col[1]
        pr = [(p - target).dot(right) for p in pts]; pu = [(p - target).dot(upv) for p in pts]
        target = target + right * (min(pr) + max(pr)) / 2 + upv * (min(pu) + max(pu)) / 2
        if size is None: size = max(max(pr) - min(pr), max(pu) - min(pu))
    fov = 2 * math.atan(18 / lens)
    dist = (size / 2 * 1.12) / math.tan(fov / 2) + size * 0.3
    CAM.location = target + d * dist; CAM.rotation_euler = rot.to_euler()
    print("CAMDBG", name, round(size,3), round(dist,3), tuple(round(x,3) for x in target), flush=True)
    if os.environ.get("DRY"):
        print("LOC", [(o.name, tuple(round(x,3) for x in o.matrix_world.translation)) for o in (HAM, CHI)]); return
    sc.render.filepath = path; bpy.ops.render.render(write_still=True); print("RENDERED", name, flush=True)

views = {}
def hv(n, *a, **k): views["hammer_" + n] = ("H", a, k)
def cv(n, *a, **k): views["chisel_" + n] = ("C", a, k)
hv("front", (0, -1, 0.04)); hv("side", (1, 0, 0.04)); hv("34", (0.62, -0.72, 0.30))
hv("top", (0.15, -0.25, 1.0)); hv("head", (0.55, -0.75, 0.38), target=(0, 0, 0.29), size=0.16)
hv("grip", (0.5, -0.8, 0.25), target=(0, 0, 0.075), size=0.16)
cv("front", (0, -1, 0.04)); cv("side", (1, 0, 0.04)); cv("34", (0.62, -0.72, 0.30))
cv("end", (0.2, -0.35, 1.0)); cv("head", (0.55, -0.75, 0.45), size=0.065)
cv("tip", (0.9, -0.42, 0.22), size=0.055)
views["hero"] = ("B", (), {})
views["hammer_site"] = ("H", (0.62, -0.72, 0.30), {})
views["chisel_site"] = ("C", (0.62, -0.72, 0.30), {})

names = list(views) if want == "all" else want.split(",")
for n in names:
    kind, a, k = views[n]
    if kind == "H":
        show(HAM); place(HAM); objs = kids(HAM)
    elif kind == "C":
        show(CHI); place(CHI); objs = kids(CHI)
    if kind == "C" and n == "chisel_head": k = dict(k, target=CENTER + V((0, 0, 0.101)))
    if kind == "C" and n == "chisel_tip": k = dict(k, target=CENTER + V((0, 0, -0.103)))
    if kind == "B":
        show(HAM, CHI)
        # strike moment: chisel tip on the stone, hammer face just above the chisel head
        a = math.radians(-18); b = a - math.radians(90)
        uc = V((math.sin(a), 0, math.cos(a)))
        Rz = Matrix.Rotation(math.radians(28), 4, 'Z')
        tip = V((0.03, 0, 0.02))
        Mc = Matrix.Translation(tip) @ Matrix.Rotation(a, 4, 'Y')
        face_local = V((-0.0603, 0, 0.295))
        Rb = Matrix.Rotation(b, 4, 'Y')
        target = tip + uc * (0.2403 + 0.012)
        Mh = Matrix.Translation(target - (Rb @ face_local)) @ Rb
        CHI.matrix_world = Rz @ Mc; HAM.matrix_world = Rz @ Mh; bpy.context.view_layer.update()
        shoot(n, (0.3, -1.0, 0.22), objs=kids(HAM) + kids(CHI), lens=70); continue
    if n.endswith("_site"):
        sc.render.resolution_x = sc.render.resolution_y = 1600
        shoot(n, a, objs=objs, **k)
        sc.render.resolution_x = sc.render.resolution_y = RES; continue
    shoot(n, *a, objs=objs, **k)
print("DONE")
