import numpy as np
co=np.load("/tmp/claude-0/-home-user-kardonov-site/cb30cd45-1b88-5b9b-b3ff-480343f6cfce/scratchpad/out/cyber2/armco.npy")
co=co[co[:,0]<-0.09]
Xw=np.array([-0.707,0.707,0]); Dd=np.array([-0.707,-0.707,0])
for z in np.arange(0.52,0.415,-0.005):
    c=co[np.abs(co[:,2]-z)<0.0025]
    if len(c)<5: continue
    w=c@Xw-0.1223; d=c@Dd-0.1251
    # histogram over w bins of dorsal max & ventral min
    bins=np.arange(-0.054,0.018,0.006); row=[]
    for b0 in bins:
        m=(w>=b0)&(w<b0+0.006)
        row.append("%5.1f/%5.1f"%(d[m].max()*1000,d[m].min()*1000) if m.sum()>3 else "    --     ")
    print("%.3f w[%.4f,%.4f]"%(z,w.min(),w.max())," ".join(row))
print("bins", np.arange(-0.054,0.018,0.006))
print("W proj", np.array([-0.175,-0.002,0.502])@Xw, np.array([-0.175,-0.002,0.502])@Dd)
