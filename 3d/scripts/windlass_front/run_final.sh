#!/bin/bash
# FINAL front-view windlass layers (Cycles 64 spp + OIDN, 3200x8192 canvas, 100%). Resumable chain:
# each blender run < 8 min (timeout 470, stops starting strips after BUDGET s); rerun this script after a container
# restart - finished strips/layers are skipped. Light/grade values = approved draft d30 (drafts/preview.jpg).
# usage: bash run_final.sh            (loops until every layer is stitched; log: out/windlass_front/final/chain.log)
S=/tmp/claude-0/-home-user-kardonov-site/cb30cd45-1b88-5b9b-b3ff-480343f6cfce/scratchpad
OUT=$S/out/windlass_front/final; mkdir -p $OUT
export KEY=3.2 SKY=0.6 BOUNCE=0.25 WORLD=0.06 RIM=2.2 EXPO=-0.25 ELEV=13 MARBLE_SAT=0.3 WOOD_SAT=0.7 ROPE_SAT=0.7 SSS=burley DIFF=1
export STRIPS=1 BUDGET=${BUDGET:-200} STRIP_H_BLOCK=96 STRIP_H_WL=490 OV=16 THREADS=${THREADS:-3}
SPP=${SPP:-64}
cd $S/assets
for run in $(seq 1 80); do
  if [ -f $OUT/strips_manifest.json ]; then
    r=$(python3 -I $S/scripts/windlass_front/stitch_layers.py $OUT); echo "$(date +%T) $r" >> $OUT/chain.log
    case "$r" in *"MISSING 0") break;; esac
  fi
  echo "$(date +%T) run $run" >> $OUT/chain.log
  timeout 470 /opt/blender/blender-4.2.3-linux-x64/blender -b scene_windlass_front.blend \
    -P $S/scripts/windlass_front/front_layers.py -- $OUT $SPP 100 >> $OUT/render.log 2>&1
  grep -E "^TIME|BUDGET|ALL STRIPS" $OUT/render.log | tail -n 3 >> $OUT/chain.log
done
# check composite (top / lowered) at 25%
python3 -I -c "
import sys; sys.argv=['x','$OUT','25','$OUT/composite_check.jpg']; exec(open('$S/scripts/windlass_front/composite.py').read())" >> $OUT/chain.log 2>&1
echo "$(date +%T) FINAL DONE" >> $OUT/chain.log
