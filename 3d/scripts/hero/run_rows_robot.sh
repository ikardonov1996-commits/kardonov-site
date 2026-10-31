#!/bin/bash
# robot-side alternative FINAL chain (resumable): glow passes (0.85 scale) + adaptive row strips (hero_final_rows.py).
# Usage: JOBS="E -55,A -47" run_rows_robot.sh
B=/opt/blender/blender-4.2.3-linux-x64/blender; S=/tmp/claude-0/-home-user-kardonov-site/cb30cd45-1b88-5b9b-b3ff-480343f6cfce/scratchpad
OUTDIR=$S/out/hero/final_robot; LOG=$OUTDIR/final.log; mkdir -p $OUTDIR/strips; cd $S/out/hero
exec 9>$OUTDIR/rows.lock; flock -n 9 || { echo "already running"; exit 0; }
IFS=',' read -ra JL <<< "$JOBS"
for job in "${JL[@]}"; do      # glow layers + probe first (cheap)
  set -- $job
  [ -f $OUTDIR/$1_glowraw_champ.png ] && continue
  env SHOT=$1 ROT=$2 VAR=42 SCALE=0.85 SPP=16 MODE=glow OUTDIR=$OUTDIR ENGINE_HINT=CYCLES timeout 470 $B -b hero_work.blend \
    -P $S/scripts/hero/hero_final_run.py 2>&1 | grep -E "GLOW_DONE|SKIP|Traceback|Error" >> $LOG
done
for job in "${JL[@]}"; do
  set -- $job
  for try in $(seq 1 300); do
    r=$(env START=0 SPR0=7 TARGET=${TARGET:-300} OV=6 ADAPT=0.015 SPP=192 SHOT=$1 ROT=$2 VAR=42 SCALE=1.6667 MODE=beauty OUTDIR=$OUTDIR \
      timeout 470 $B -b hero_work.blend -P $S/scripts/hero/hero_final_rows.py 2>&1 | grep -E "ROWS_|PREV_TIMEOUT|Traceback|Error")
    echo "$r" >> $LOG; rm -f $OUTDIR/strips/*.tmp.png
    echo "$r" | grep -q ROWS_ALL_DONE && break
    echo "$r" | grep -q Traceback && { echo "FAIL $1" >> $LOG; break; }
  done
  echo "SHOT_DONE $1 $(date +%T)" >> $LOG
done
echo "ROWS_CHAIN_DONE $(date +%T)" >> $LOG
