# overlay 1cm world grid on ortho renders; args: prefix cx,cy,cz,size out
import sys
from PIL import Image, ImageDraw
pre, cen, out = sys.argv[1], [float(v) for v in sys.argv[2].split(",")], sys.argv[3]
size=cen[3]; RIGHT={'mY':(0,1),'mX':(1,-1),'pY':(0,-1),'pX':(1,1)}
ims=[]
for v in ['mY','mX','pY','pX']:
    im=Image.open(f"{pre}_{v}.png").convert('RGB'); W=im.width; d=ImageDraw.Draw(im)
    ax,sg=RIGHT[v]; c=cen[ax]; s=W/size
    import math
    lo=c-size/2; hi=c+size/2
    k=math.ceil(lo*100)
    while k/100<hi:
        x=(k/100-c)*sg*s+W/2; d.line([(x,0),(x,W)],fill=(255,0,0) if k%5==0 else (120,40,40)); 
        if k%2==0: d.text((x+2,2),"%d"%k,fill=(255,255,0))
        k+=1
    lo=cen[2]-size/2; k=math.ceil(lo*100)
    while k/100<cen[2]+size/2:
        y=W/2-(k/100-cen[2])*s; d.line([(0,y),(W,y)],fill=(255,0,0) if k%5==0 else (120,40,40)); d.text((2,y+2),"z%d"%k,fill=(0,255,255)); k+=1
    d.text((W-200,W-20),v+(" right=+" if sg>0 else " right=-")+"XYZ"[ax],fill=(255,255,255))
    ims.append(im)
S=Image.new('RGB',(ims[0].width*2,ims[0].height*2))
for i,im in enumerate(ims): S.paste(im,((i%2)*im.width,(i//2)*im.height))
S.save(out)
