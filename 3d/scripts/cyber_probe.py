import bpy, numpy as np
for o in bpy.data.objects:
    print(o.name, o.type, o.parent.name if o.parent else None, tuple(round(v,3) for v in o.location), tuple(round(v,3) for v in o.rotation_euler), tuple(round(v,3) for v in o.scale), o.data.name if o.data else None)
sc=bpy.context.scene
print("engine", sc.render.engine, sc.render.resolution_x, sc.render.resolution_y, sc.camera.name)
o=bpy.data.objects["Sculpture_HiRes"]
print("mods", [m.type for m in o.modifiers], "mats", [m.name for m in o.data.materials], dict(o.items()) if o.keys() else None)
print(o.matrix_world)
me=o.data; print("verts", len(me.vertices), "polys", len(me.polygons))
co=np.empty(len(me.vertices)*3); me.vertices.foreach_get('co',co); co=co.reshape(-1,3)
print("bbox", co.min(0), co.max(0))
# slices on viewer-left side x<0
for z in np.arange(0.40,1.0,0.02):
    m=(np.abs(co[:,2]-z)<0.004)
    P=co[m]
    # cluster by x
    xs=np.sort(P[:,0])
    gaps=np.where(np.diff(xs)>0.01)[0]
    segs=[]; st=0
    for g in list(gaps)+[len(xs)-1]:
        segs.append((xs[st],xs[g])); st=g+1
    print("z=%.2f"%z, " ".join("[%.3f,%.3f]"%s for s in segs))
