#!/bin/bash
# stage 6 FINAL (resumable; rerun after a container restart): 16 strips 1080x1440 64 spp adaptive .015 + OIDN -> glow pass -> post
#   setsid nohup scripts/stage6/chain6.sh >> out/stage6/final6.log 2>&1 &
S=/tmp/claude-0/-home-user-kardonov-site/cb30cd45-1b88-5b9b-b3ff-480343f6cfce/scratchpad; B=/opt/blender/blender-4.2.3-linux-x64/blender
F=$S/out/stages_light/final; W6=$S/out/stage6/stage6_work.blend
exec 9>$S/out/stage6/chain6.lock; flock -n 9 || { echo "already running"; exit 0; }
export NSTRIP=16 ADAPT=0.015
for run in $(seq 1 200); do
  [ -f $F/stage_6.png ] && break
  echo "run $run $(date +%T)"
  cd $S/out/stage6 && timeout 470 nice -n 5 $B -b $W6 -P $S/scripts/stage6/stage6.py -- render6 $F 1080 1440 64 2>&1 | grep --line-buffered -E "STRIP|STILL|Error|Traceback"
  rm -f $F/parts/stage_6_s*.part.png
done
cp -f $F/stage_6.png $F/stage_6_Cyber_David.png
for run in 1 2 3; do
  [ -f $F/stage_6_glowraw_champ.png ] && break
  cd $S/out/stage6 && timeout 470 nice -n 5 $B -b $W6 -P $S/scripts/stage6/stage6.py -- glow6 $F 1080 1440 2>&1 | grep --line-buffered -E "GLOW|Error|Traceback"
done
rm -f $F/stage_6_glowpass_beauty.png
python3 $S/scripts/stage6/post6.py
python3 $S/scripts/stages_light/seamcheck.py $F/stage_6_Cyber_David.png $F/stage_5_Sculpture_HiRes.png
echo "CHAIN6 DONE $(date +%T)"
