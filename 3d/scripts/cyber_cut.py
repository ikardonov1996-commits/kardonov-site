# Stage 1: cut the hanging right arm off Sculpture_HiRes with a shoulder plane; keep the removed
# arm as ArmRef (reference for building the robot arm), cap the shoulder with a recessed cap.
import bpy, bmesh, numpy as np, sys, time
from mathutils import Vector
argv=sys.argv[sys.argv.index("--")+1:]; OUT=argv[0]
t0=time.time()
ob=bpy.data.objects["Sculpture_HiRes"]; me=ob.data
P0=Vector((-0.108,0,0.70)); N=Vector((-0.994,0,0.108)).normalized()
bm=bmesh.new(); bm.from_mesh(me)
bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
reg=[f for f in bm.faces if any((v.co.x<-0.07 and 0.60<v.co.z<0.845) for v in f.verts)]
edges=set(e for f in reg for e in f.edges); verts=set(v for f in reg for v in f.verts)
geom=list(verts)+list(edges)+reg
r=bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-6, plane_co=P0, plane_no=N)
cutv=set(e for e in r['geom_cut'] if isinstance(e,bmesh.types.BMVert))
print("bisect", len(cutv), time.time()-t0)
# separate along cut: mark outer faces in region
def outer(f):
    c=f.calc_center_median(); return (c-P0).dot(N)>0
# flood fill from hand face without crossing cut verts' edges on plane
bm.faces.ensure_lookup_table()
hand=Vector((-0.172,-0.005,0.475))
seed=min((f for f in bm.faces if (f.calc_center_median()-hand).length<0.02), key=lambda f:(f.calc_center_median()-hand).length)
cutedges=set(e for e in bm.edges if e.verts[0] in cutv and e.verts[1] in cutv)
seen={seed}; st=[seed]
while st:
    f=st.pop()
    for e in f.edges:
        if e in cutedges: continue
        for g in e.link_faces:
            if g not in seen: seen.add(g); st.append(g)
for f in reg:
    if f.is_valid and f not in seen:
        c=f.calc_center_median()
        if 0.64<c.z<0.84 and (c-P0).dot(N)>0: seen.add(f)
print("arm faces", len(seen), "of", len(bm.faces), time.time()-t0)
if len(seen)>len(bm.faces)*0.3: raise SystemExit("cut leaked")
# build ArmRef mesh from those faces
armbm=bmesh.new(); vmap={}
for f in seen:
    vs=[]
    for v in f.verts:
        if v not in vmap: vmap[v]=armbm.verts.new(v.co)
        vs.append(vmap[v])
    armbm.faces.new(vs)
am=bpy.data.meshes.new("ArmRef"); armbm.to_mesh(am); armbm.free()
arm=bpy.data.objects.new("ArmRef", am); bpy.context.scene.collection.objects.link(arm)
bmesh.ops.delete(bm, geom=list(seen), context='FACES')
loose=[v for v in bm.verts if not v.link_faces]; bmesh.ops.delete(bm, geom=loose, context='VERTS')
# cap the hole: boundary edges near the plane
bnd=[e for e in bm.edges if e.is_boundary]
print("boundary edges", len(bnd))
r=bmesh.ops.holes_fill(bm, edges=bnd, sides=0)
newf=r['faces']; print("filled", len(newf))
bmesh.ops.triangulate(bm, faces=newf, quad_method='BEAUTY', ngon_method='BEAUTY')
bm.to_mesh(me); bm.free(); me.update()
print("done", len(me.vertices), time.time()-t0)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
