#!/bin/bash
# resumable: ev6.py skips existing cy6_*.png
S=/tmp/claude-0/-home-user-kardonov-site/cb30cd45-1b88-5b9b-b3ff-480343f6cfce/scratchpad
cd $S/out/cyber6
/opt/blender/blender-4.2.3-linux-x64/blender -b build6.blend -P $S/scripts/c6/ev6.py -- $S/out/cyber6/cy6 ${VIEWS6:-02_main34,07_hand_front,08_hand_back,h6_front,h6_back,h6_side,h6_thumb,01_front,03_armside,04_armfront,05_shoulder_front,06_shoulder_back,12_elbow_inner,09_band_front,10_band_back,11_band_34,13_band_left,14_band_right} 600x800 16 >> render.log 2>&1
echo RENDER_DONE >> render.log
