#!/bin/bash
# resumable chain: re-launches blender (<8 min per run) until all requested stills exist.
# usage: chain.sh OUTDIR W H SPP [stages] ; env NSTRIP, LIGHT_OVR passed through
S=/tmp/claude-0/-home-user-kardonov-site/cb30cd45-1b88-5b9b-b3ff-480343f6cfce/scratchpad
OUT=$1; W=$2; H=$3; SPP=$4; ST=${5:-1,2,3,4,5}
mkdir -p "$OUT"
for run in $(seq 1 400); do
  miss=0; for i in ${ST//,/ }; do [ -f "$OUT/stage_$i.png" ] || miss=1; done
  [ $miss = 0 ] && { echo "CHAIN DONE"; exit 0; }
  echo "run $run $(date +%T)"
  cd $S/out/stages_light && timeout 470 nice -n 5 /opt/blender/blender-4.2.3-linux-x64/blender -b stages_work.blend \
    -P $S/scripts/stages_light/stages_light.py -- render "$OUT" $W $H $SPP $ST 2>&1 | grep --line-buffered -E "STRIP|STILL|Error|Traceback"
done
