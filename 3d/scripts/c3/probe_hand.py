import numpy as np
co=np.load("/tmp/claude-0/-home-user-kardonov-site/cb30cd45-1b88-5b9b-b3ff-480343f6cfce/scratchpad/out/cyber2/armco.npy")
for z in np.arange(0.80,0.39,-0.01):
    m=(co[:,2]>z-0.005)&(co[:,2]<z+0.005)&(co[:,0]<-0.09)
    if m.sum()<5: print(round(z,3),"none"); continue
    c=co[m]; print(round(z,3), m.sum(), "x %.4f..%.4f y %.4f..%.4f"%(c[:,0].min(),c[:,0].max(),c[:,1].min(),c[:,1].max()))
