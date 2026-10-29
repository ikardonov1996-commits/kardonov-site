# usage: hortho.sh blend prefix
cd /tmp/claude-0/-home-user-kardonov-site/cb30cd45-1b88-5b9b-b3ff-480343f6cfce/scratchpad/out/cyber8/an; /opt/blender/blender-4.2.3-linux-x64/blender -b $1 -P /tmp/claude-0/-home-user-kardonov-site/cb30cd45-1b88-5b9b-b3ff-480343f6cfce/scratchpad/scripts/c8/ghost.py -P /tmp/claude-0/-home-user-kardonov-site/cb30cd45-1b88-5b9b-b3ff-480343f6cfce/scratchpad/scripts/c8/ortho.py -- /tmp/claude-0/-home-user-kardonov-site/cb30cd45-1b88-5b9b-b3ff-480343f6cfce/scratchpad/out/cyber8/an/$2 Robo_Hand,Robo_WristJoint,Robo_Indicators,ArmRef -0.160,-0.004,0.465,0.11 -Y,-X,+X,-Z,+Y MAT >/dev/null 2>&1
python3 -c "
from PIL import Image
s=Image.new('RGB',(1500,1000))
for i,f in enumerate(['mY','mX','pX','mZ','pY']): s.paste(Image.open('$2_'+f+'.png').resize((500,500)),((i%3)*500,(i//3)*500))
s.save('$2_all.png')"
