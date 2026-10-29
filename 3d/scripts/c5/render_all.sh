#!/bin/bash
# resumable: ev.py skips existing cy5_*.png
cd /tmp/claude-0/-home-user-kardonov-site/cb30cd45-1b88-5b9b-b3ff-480343f6cfce/scratchpad/out/cyber5
/opt/blender/blender-4.2.3-linux-x64/blender -b build5.blend -P /tmp/claude-0/-home-user-kardonov-site/cb30cd45-1b88-5b9b-b3ff-480343f6cfce/scratchpad/scripts/c5/ev.py -- /tmp/claude-0/-home-user-kardonov-site/cb30cd45-1b88-5b9b-b3ff-480343f6cfce/scratchpad/out/cyber5/cy5 01_front,02_main34,03_armside,04_armfront,05_shoulder_front,06_shoulder_back,07_hand_front,08_hand_back,12_elbow_inner,09_band_front,10_band_back,11_band_34,13_band_left,14_band_right 600x800 14 >> render.log 2>&1
