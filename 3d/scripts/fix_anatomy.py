# Replace the over-long nipples and the protruding navel with sculpted shapes.
# In the source mesh these are separate shells stuck into the torso, so each
# feature is cut out (torso + shell), the hole is refilled with fresh mesh, and
# the patch is shaped as a smooth fit of the surrounding torso + a designed profile.
import bpy, bmesh, sys, numpy as np
from mathutils import Vector
argv=sys.argv[sys.argv.index("--")+1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
ob=bpy.data.objects["Sculpture_HiRes"]; me=ob.data
bm=bmesh.new(); bm.from_mesh(me)
fx=bm.verts.layers.int.new('fixed'); pl=bm.faces.layers.int.new('patch'); el=bm.edges.layers.int.new('rim')
def arrays():
    bm.verts.ensure_lookup_table(); bm.normal_update()
    return np.array([v.co[:] for v in bm.verts]), np.array([v.normal[:] for v in bm.verts])
co,no=arrays()
def front(x,z):
    m=(np.abs(co[:,0]-x)<0.003)&(np.abs(co[:,2]-z)<0.003)
    return co[np.where(m)[0][np.argmin(co[m,1])]]
# profiles in local tangent coords (u horizontal, v vertical), metres
def nipple(u,v):
    d=np.hypot(u,v); return 0.0010*np.exp(-(d/0.0028)**2)+0.00045*np.exp(-(d/0.0068)**2)
def navel(u,v):
    d=np.hypot(u/0.0032,v/0.0050)          # vertical oval
    pit=-0.0030*np.clip(1-d*d,0,1)**1.5
    lip=0.00035*np.exp(-((v-0.0045)/0.0016)**2)*np.exp(-(u/0.004)**2)   # soft upper fold
    return pit+lip

def fix(p, profile0, r_cut, r_ring, name, shift=(0,0,0), late=False):
    global co,no
    d=np.linalg.norm(co-p,axis=1)
    ring=np.where((d>r_ring[0])&(d<r_ring[1]))[0]
    nrm=no[ring].mean(0); nrm/=np.linalg.norm(nrm)
    t1=np.cross(nrm,[0,0,1.0]); t1/=np.linalg.norm(t1); t2=np.cross(nrm,t1)
    if t2[2]<0: t2=-t2
    def local(P): q=np.atleast_2d(P)-p; return q@t1,q@t2,q@nrm
    du,dv=np.dot(shift,t1),np.dot(shift,t2)
    prof=lambda u,v: profile0(u-du,v-dv)
    profile=(lambda u,v: 0*u) if late else prof
    u,v,h=local(co[ring]); keep=np.abs(h)<0.01
    A=lambda u,v: np.c_[np.ones_like(u),u,v,u*u,u*v,v*v]
    coef,*_=np.linalg.lstsq(A(u[keep],v[keep]),h[keep],rcond=None)
    base=lambda u,v: A(np.atleast_1d(u),np.atleast_1d(v))@coef
    def place(u,v): return Vector(p+u*t1+v*t2+(base(u,v)[0]+profile(u,v))*nrm)
    def tang(P): uu,vv,_=local(np.array(P[:])); return uu[0],vv[0]
    dead=[]
    for v in bm.verts:
        c=np.array(v.co[:])
        if np.abs(c-p).max()>r_cut*2: continue
        uu,vv,hh=local(c)
        if np.hypot(uu[0],vv[0])<r_cut and -0.010<hh[0]-base(uu,vv)[0]<0.015: dead.append(v)
    dead=list({f for v in dead for f in v.link_faces})
    bmesh.ops.delete(bm,geom=dead,context='FACES_ONLY')
    # remove leftover fragments of the old shells: small islands near the feature
    near_f={f for f in bm.faces if np.abs(np.array(f.verts[0].co[:])-p).max()<r_cut*2.5}
    seen=set(); junk=[]
    for f0 in near_f:
        if f0 in seen: continue
        comp=[f0]; seen.add(f0); stack=[f0]; escaped=False
        while stack:
            f=stack.pop()
            for e in f.edges:
                for g in e.link_faces:
                    if g not in near_f: escaped=True; continue
                    if g in seen: continue
                    seen.add(g); comp.append(g); stack.append(g)
        if not escaped: junk+=comp
    bmesh.ops.delete(bm,geom=junk,context='FACES_ONLY')
    loose=[v for v in bm.verts if not v.link_faces and np.abs(np.array(v.co[:])-p).max()<r_cut*2]
    bmesh.ops.delete(bm,geom=loose,context='VERTS')
    rim=[e for e in bm.edges if e.is_boundary and np.abs(np.array(e.verts[0].co[:])-p).max()<r_cut*2
         and np.hypot(*tang(e.verts[0].co))>r_cut*0.75]
    res=bmesh.ops.triangle_fill(bm,use_beauty=True,use_dissolve=False,edges=rim)
    patch={g for g in res['geom'] if isinstance(g,bmesh.types.BMFace)}
    for v in bm.verts: v[fx]=0
    for e in bm.edges: e[el]=0
    for e in rim:
        e[el]=1
        for v in e.verts: v[fx]=1
    for f in bm.faces: f[pl]=0
    for f in patch: f[pl]=1
    for _ in range(3):
        edges=list({e for f in patch for e in f.edges if not e[el]})
        bmesh.ops.subdivide_edges(bm,edges=edges,cuts=1,use_grid_fill=True)
        patch=[f for f in bm.faces if f[pl]==1]
        bmesh.ops.triangulate(bm,faces=patch)
        patch=[f for f in bm.faces if f[pl]==1]
    rimv={v for e in bm.edges if e[el] for v in e.verts}
    region=list({f for f in patch}|{f for v in rimv for f in v.link_faces})
    bmesh.ops.recalc_face_normals(bm,faces=region)
    inner=list({v for f in patch for v in f.verts if v not in rimv and not v.is_boundary})
    for it in range(300 if late else 100):
        for v in inner:
            if it==0: v.co=place(*tang(v.co)); continue
            avg=sum((e.other_vert(v).co for e in v.link_edges),Vector())/len(v.link_edges)
            v.co=avg if late else place(*tang(avg))   # late: membrane spanning the rim
        if it%5==0 and it>0 and not late:
            for v in rimv:
                avg=sum((e.other_vert(v).co for e in v.link_edges),Vector())/len(v.link_edges)
                v.co=v.co.lerp(place(*tang(avg)),0.5)
    lo=0.0 if late else 0.55
    band=[v for v in bm.verts if np.abs(np.array(v.co[:])-p).max()<r_cut*1.6
           and r_cut*lo<=np.hypot(*tang(v.co))<r_cut*1.25 and abs(local(np.array(v.co[:]))[2][0]-base(*tang(v.co))[0])<0.006]
    for _ in range(60 if late else 20):
        bmesh.ops.smooth_vert(bm,verts=band,factor=0.5,use_axis_x=True,use_axis_y=True,use_axis_z=True)
    if late:   # carve the designed shape into the now-smooth surface
        bm.normal_update()
        for v in band:
            uu,vv=tang(v.co); d=prof(uu,vv)
            if abs(d)>1e-6: v.co+=Vector(nrm)*float(d)
    print("band %d"%len(band)); print("%s: junk %d, cut %d faces, rim %d edges, patch %d faces, %d verts"%(name,len(junk),len(dead),len(rim),len(patch),len(inner)))
    co,no=arrays()

def smooth_carve(p, profile0, shift=(0,0,0), r_flat=0.0075, r_blend=0.0105):
    """Clean mesh: rub the old feature flat (Laplacian), then carve the new shape."""
    global co,no
    d=np.linalg.norm(co-p,axis=1)
    ring=np.where((d>0.011)&(d<0.017))[0]
    nrm=no[ring].mean(0); nrm/=np.linalg.norm(nrm)
    t1=np.cross(nrm,[0,0,1.0]); t1/=np.linalg.norm(t1); t2=np.cross(nrm,t1)
    if t2[2]<0: t2=-t2
    def tang(P): q=np.array(P[:])-p; return q@t1,q@t2
    near=[v for v in bm.verts if np.abs(np.array(v.co[:])-p).max()<r_blend and np.dot(np.array(v.co[:])-p,nrm)>-0.008]
    core=[v for v in near if np.hypot(*tang(v.co))<r_flat]
    blend=[v for v in near if np.hypot(*tang(v.co))<r_blend]
    for i in range(400):
        bmesh.ops.smooth_vert(bm,verts=core,factor=0.6,use_axis_x=True,use_axis_y=True,use_axis_z=True)
        if i%4==0: bmesh.ops.smooth_vert(bm,verts=blend,factor=0.3,use_axis_x=True,use_axis_y=True,use_axis_z=True)
    du,dv=np.dot(shift,t1),np.dot(shift,t2)
    for v in core:
        uu,vv=tang(v.co); h=profile0(uu-du,vv-dv)
        if abs(h)>1e-7: v.co+=Vector(nrm)*float(h)
    pit=[v for v in core if np.hypot(*tang(v.co))<0.0065]
    for _ in range(3):
        bmesh.ops.smooth_vert(bm,verts=pit,factor=0.4,use_axis_x=True,use_axis_y=True,use_axis_z=True)
    print("navel: rubbed %d verts, carved"%len(core))
    co,no=arrays()

fix(front(-0.0800,0.7180),nipple,0.0105,(0.0125,0.019),"nipple R")
fix(front( 0.0427,0.7385),nipple,0.0105,(0.0125,0.019),"nipple L")
smooth_carve(front(-0.0132,0.6300),navel,shift=(0.0037,0,0))   # navel onto abs midline (x=-0.011)
fix(front(-0.0900,0.7600),lambda u,v: 0*u,0.0065,(0.0085,0.014),"bump above R nipple")
bm.to_mesh(me); me.update()
me.polygons.foreach_set('use_smooth',[True]*len(me.polygons))
bpy.ops.wm.save_as_mainfile(filepath=argv[0],compress=True)
