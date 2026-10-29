# it.sh TAG [views] : quick build + render iteration into out/cyber9/it (env T_* passed through)
S=/tmp/claude-0/-home-user-kardonov-site/cb30cd45-1b88-5b9b-b3ff-480343f6cfce/scratchpad
B=/opt/blender/blender-4.2.3-linux-x64/blender
cd $S/assets && $B -b asset_statue_cyber_v1.blend -P $S/scripts/c9/build9.py -- $S/out/cyber/stage_cut.blend $S/out/cyber9/it/$1.blend > $S/out/cyber9/it/$1.log 2>&1
grep -E "thumb v8|thenar root|CMC housing|CLEAR|Traceback|Error" $S/out/cyber9/it/$1.log
cd $S/out/cyber9/it && FORCE=1 $B -b $1.blend -P $S/scripts/c9/ev9.py -- $S/out/cyber9/it/$1 ${2:-h6_thumb,h6_back,h6_front,h6_side} 450x600 8 > $1.r.log 2>&1
python3 -c "
from PIL import Image
v='${2:-h6_thumb,h6_back,h6_front,h6_side}'.split(',')
s=Image.new('RGB',(450*len(v),600))
for i,f in enumerate(v): s.paste(Image.open('$1_'+f+'.png'),(i*450,0))
s.save('$1_all.png')"
