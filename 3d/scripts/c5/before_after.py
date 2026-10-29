import sys
from PIL import Image, ImageDraw
a,b,out=sys.argv[1:4]
A=Image.open(a).convert('RGB'); B=Image.open(b).convert('RGB').resize(A.size)
s=Image.new('RGB',(A.width*2,A.height)); s.paste(A,(0,0)); s.paste(B,(A.width,0))
d=ImageDraw.Draw(s); d.text((10,10),"v4 (Tool_Gunmetal, dense neon)",fill=(255,255,0)); d.text((A.width+10,10),"v5 (AI_Titanium, clean neon, amber halo)",fill=(255,255,0))
s.save(out)
