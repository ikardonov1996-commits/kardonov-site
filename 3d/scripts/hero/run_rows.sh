#!/bin/bash
# resumable hero FINAL beauty chain (adaptive row strips). Usage: run_rows.sh  (jobs: "SHOT ROT START SPR0")
B=/opt/blender/blender-4.2.3-linux-x64/blender; S=/tmp/claude-0/-home-user-kardonov-site/cb30cd45-1b88-5b9b-b3ff-480343f6cfce/scratchpad
OUTDIR=$S/out/hero/final; LOG=$OUTDIR/final.log; cd $S/out/hero
exec 9>$OUTDIR/rows.lock; flock -n 9 || { echo "already running"; exit 0; }
for job in "E 0 473 7" "A 10 0 7"; do
  set -- $job
  for try in $(seq 1 300); do
    r=$(env START=$3 SPR0=$4 TARGET=${TARGET:-300} OV=6 ADAPT=0.015 SPP=192 SHOT=$1 ROT=$2 VAR=42 SCALE=1.6667 MODE=beauty OUTDIR=$OUTDIR \
      timeout 470 $B -b hero_work.blend -P $S/scripts/hero/hero_final_rows.py 2>&1 | grep -E "ROWS_|PREV_TIMEOUT|Traceback|Error")
    echo "$r" >> $LOG; rm -f $OUTDIR/strips/*.tmp.png
    echo "$r" | grep -q ROWS_ALL_DONE && break
    echo "$r" | grep -q Traceback && { echo "FAIL $1" >> $LOG; break; }
  done
  echo "SHOT_DONE $1 $(date +%T)" >> $LOG
done
echo "ROWS_CHAIN_DONE $(date +%T)" >> $LOG
