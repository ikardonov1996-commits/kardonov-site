#!/bin/bash
# headtest.sh TAG "LIGHT_OVR" stages...
S=/tmp/claude-0/-home-user-kardonov-site/cb30cd45-1b88-5b9b-b3ff-480343f6cfce/scratchpad; T=$1; OV=$2; shift 2
mkdir -p $S/out/stages_light/headtest; cd $S/out/stages_light
for i in "$@"; do f=$S/out/stages_light/headtest/${T}_s$i.png; [ -f $f ] && continue
LIGHT_OVR="$OV" timeout 470 nice -n 5 /opt/blender/blender-4.2.3-linux-x64/blender -b stages_work.blend -P $S/scripts/stages_light/stages_light.py -- headtest $f $i 2>&1 | grep -E "HEAD|Error|Traceback" -A3; done
