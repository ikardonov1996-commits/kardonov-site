import sys, os
from PIL import Image, ImageDraw
out=sys.argv[1]; fs=sys.argv[2:]; ims=[Image.open(f).convert('RGB').resize((360,480)) for f in fs]
cols=6; rows=(len(ims)+cols-1)//cols; s=Image.new('RGB',(360*cols,480*rows),(20,20,20)); d=ImageDraw.Draw(s)
for i,(im,f) in enumerate(zip(ims,fs)):
    x,y=(i%cols)*360,(i//cols)*480; s.paste(im,(x,y)); d.text((x+6,y+6),os.path.basename(f)[4:-4],fill=(255,255,0))
s.save(out)
