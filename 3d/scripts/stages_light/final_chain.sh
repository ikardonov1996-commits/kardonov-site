#!/bin/bash
# FINAL stage stills -- run ONLY after the client approves the drafts (out/stages_light/stages_draft_strip.jpg).
# Same scene/camera/light as the drafts (defaults in stages_light.py), 1080x1440 RGBA transparent PNG, Cycles CPU,
# 64 spp adaptive 0.015 + OIDN (old site stills: 48 spp / 0.02). Resumable: each still = 16 horizontal strips
# (out/stages_light/final/parts/), every blender run < 8 min (timeout 470 + internal budget), so after a container
# restart just run this script again (nohup ... &) -> it continues from the missing strips; stitched to final/stage_{1..5}.png.
#   nohup scripts/stages_light/final_chain.sh > out/stages_light/final_chain.log 2>&1 &
# env: RES=1440x1920 (x1.8 time, own folder final_1440x1920), SPP=96, STAGES=1,2 (subset/order)
S=/tmp/claude-0/-home-user-kardonov-site/cb30cd45-1b88-5b9b-b3ff-480343f6cfce/scratchpad
RES=${RES:-1080x1440}; W=${RES%x*}; H=${RES#*x}
OUT=$S/out/stages_light/final$([ "$RES" != 1080x1440 ] && echo "_$RES")
export NSTRIP=${NSTRIP:-16} ADAPT=${ADAPT:-0.015}
exec $S/scripts/stages_light/chain.sh "$OUT" $W $H ${SPP:-64} ${STAGES:-1,2,3,4,5}
