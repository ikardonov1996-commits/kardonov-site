import bpy, sys, numpy as np
argv=sys.argv[sys.argv.index("--")+1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
me=bpy.data.objects["Sculpture_HiRes"].data
co=np.empty(len(me.vertices)*3); me.vertices.foreach_get('co',co); co=co.reshape(-1,3)
for z in [0.60,0.615,0.645,0.66,0.675,0.69,0.71]:
    xs=np.arange(-0.05,0.03,0.0015); ys=[]
    for x in xs:
        m=(np.abs(co[:,0]-x)<0.0008)&(np.abs(co[:,2]-z)<0.0015)&(co[:,1]<0)
        ys.append(co[m,1].min() if m.any() else np.nan)
    ys=np.array(ys)
    # groove = local maximum of y (surface recedes); smooth a little
    k=np.convolve(np.nan_to_num(ys,nan=-1),np.ones(3)/3,'same')
    cand=[i for i in range(2,len(xs)-2) if k[i]>=k[i-1] and k[i]>=k[i+1] and k[i]>=k[i-2] and k[i]>=k[i+2]]
    print("z=%.3f grooves at x="%z, [round(xs[i],4) for i in cand], " front-most x=%.4f"%xs[np.nanargmin(ys)])
