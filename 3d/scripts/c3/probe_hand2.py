import numpy as np
co=np.load("/tmp/claude-0/-home-user-kardonov-site/cb30cd45-1b88-5b9b-b3ff-480343f6cfce/scratchpad/out/cyber2/armco.npy")
for lo,hi in ((0.465,0.495),(0.455,0.50),(0.42,0.45)):
    m=(co[:,2]>lo)&(co[:,2]<hi)&(co[:,0]<-0.09); c=co[m]; mu=c.mean(0)
    w,v=np.linalg.eigh(np.cov((c-mu).T)); print(lo,hi,"mean",mu.round(4))
    for k in (2,1,0):
        a=v[:,k]; pr=(c-mu)@a; print("  axis",a.round(3),"extent %.4f..%.4f"%(pr.min(),pr.max()))
# lowest points (finger tips)
m=(co[:,2]<0.43)&(co[:,0]<-0.09); print("tips mean",co[m].mean(0).round(4), co[m].min(0).round(4), co[m].max(0).round(4))
