import sys, os
from PIL import Image, ImageDraw
out=sys.argv[1]; cols=int(sys.argv[2]); fs=sys.argv[3:]; W,H=450,600
ims=[Image.open(f).convert('RGB').resize((W,H)) for f in fs]
rows=(len(ims)+cols-1)//cols; s=Image.new('RGB',(W*cols,H*rows),(15,15,18)); d=ImageDraw.Draw(s)
for i,(im,f) in enumerate(zip(ims,fs)):
    x,y=(i%cols)*W,(i//cols)*H; s.paste(im,(x,y)); d.text((x+6,y+6),os.path.basename(f)[:-4],fill=(255,255,0))
s.save(out)
