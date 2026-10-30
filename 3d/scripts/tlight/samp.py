import sys, numpy as np; from PIL import Image
d=sys.argv[1]; k=800/700
h=np.asarray(Image.open(d+'/r_hammer_site.png').convert('RGB')).astype(int)
c=np.asarray(Image.open(d+'/r_chisel_site.png').convert('RGB')).astype(int)
s=lambda b: tuple(int(v*k) for v in b)
for nm,b,im,off in [('leather',(335,420,360,520),h,0),('marble shaft',(338,250,358,330),h,0),('marble panel',(275,115,295,170),h,0),('gold head end',(395,110,440,170),h,0),('ti body',(1040,200,1055,450),c,700),('ti head',(1030,75,1075,140),c,700),('blade',(1035,490,1065,580),c,700)]:
    x0,y0,x1,y1=s((b[0]-off,b[1],b[2]-off,b[3])); r=im[y0:y1,x0:x1].reshape(-1,3); print(nm,r.mean(0).round(), np.percentile(r.max(1),99))
