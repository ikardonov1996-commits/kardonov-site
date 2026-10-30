import sys; from PIL import Image
d=sys.argv[1]+'/'
def od(n):
    im=Image.open(d+'r_'+n+'.png').convert('RGBA'); bg=Image.new('RGBA',im.size,(15,15,18,255)); bg.alpha_composite(im); return bg.convert('RGB')
h=od('hammer_site'); c=od('chisel_site')
a=h.crop((200,40,600,440)); b=c.crop((300,0,600,300)).resize((400,400)); e=c.crop((330,380,530,780)).resize((200,400))
f=h.crop((240,380,640,780))
out=Image.new('RGB',(1400,400)); out.paste(a,(0,0)); out.paste(b,(400,0)); out.paste(e,(800,0)); out.paste(f,(1000,0)); out.save(d+'_crop.jpg',quality=92)
