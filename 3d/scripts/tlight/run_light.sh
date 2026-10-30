#!/bin/bash
# KARDONOV tools relight chain (resumable: every step skips existing outputs; each blender call < 8 min)
# usage: run_light.sh RES SPP OUTDIR      drafts: 800 96 out/tools_light/draft3     finals: 1600 128 out/tools_light/final
# SPLIT=1 (default for RES>=1600): beauty views rendered as horizontal bands (hammer NB_HAMMER=4, chisel NB_CHISEL=2) (BORDER) and merged -> each call ~3-5 min
# after the renders: python3 scripts/tlight/tools_light_post.py OUTDIR   (glow layers, previews, profiles.json + key-point check)
S=/tmp/claude-0/-home-user-kardonov-site/cb30cd45-1b88-5b9b-b3ff-480343f6cfce/scratchpad
B=/opt/blender/blender-4.2.3-linux-x64/blender; R=$S/scripts/tlight/tools_light_render.py
RES=${1:-800}; SPP=${2:-96}; O=${3:-$S/out/tools_light/draft}; mkdir -p $O
SPLIT=${SPLIT:-$([ $RES -ge 1600 ] && echo 1 || echo 0)}
cd $S/assets
run() {   # run <prefix> <view> <out> [env...]
  local pre=$1 v=$2 out=$3; shift 3
  [ -s "$out" ] && { echo "skip $out"; return 0; }
  local t0=$(date +%s); echo "$(date +%T) start $pre $v $*"
  env "$@" timeout 470 $B -b asset_tools_light.blend -P $R -- $O/$pre $v $RES $SPP 0 >> $O/log_${pre}_${v}.txt 2>&1
  [ -s "$out" ] && echo "$(date +%T) done $out ($(( $(date +%s)-t0 )) s)" || { echo "$(date +%T) FAILED $out (rerun the chain to resume)"; return 1; }
}
for v in hammer_site chisel_site hammer_profile chisel_profile; do
  nb=1; [ "$SPLIT" = 1 ] && { [[ $v == hammer_* ]] && nb=${NB_HAMMER:-4} || nb=${NB_CHISEL:-2}; }
  if [ $nb -gt 1 ]; then
    [ -s $O/r_$v.png ] && { echo "skip $O/r_$v.png"; continue; }
    args=(); ok=1
    for ((i=0;i<nb;i++)); do
      y0=$(python3 -c "print(round($i/$nb,4))"); y1=$(python3 -c "print(round(($i+1)/$nb,4))")
      run rb$i $v $O/rb${i}_$v.png BORDER=$y0,$y1 || { ok=0; break; }
      args+=($O/rb${i}_$v.png:$y0,$y1)
    done
    [ $ok = 1 ] && python3 $S/scripts/tlight/merge_bands.py $O/r_$v.png "${args[@]}" && { [ -f $O/rb0_$v.json ] && cp $O/rb0_$v.json $O/r_$v.json; true; }
  else run r $v $O/r_$v.png; fi
done
for v in hammer_site chisel_site hammer_profile chisel_profile; do run glowraw $v $O/glowraw_$v.png GLOW=1; done
n=$(ls $O/r_*.png $O/glowraw_*.png 2>/dev/null | wc -l); [ "$n" = 8 ] && echo ALLDONE > $O/done.flag && echo ALLDONE
