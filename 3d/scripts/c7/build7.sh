S=/tmp/claude-0/-home-user-kardonov-site/cb30cd45-1b88-5b9b-b3ff-480343f6cfce/scratchpad
cd $S/assets && /opt/blender/blender-4.2.3-linux-x64/blender -b asset_statue_cyber_v1.blend -P $S/scripts/c7/build7.py -- $S/out/cyber/stage_cut.blend ${1:-$S/out/cyber7/build7.blend} > $S/out/cyber7/build.log 2>&1
grep -E "^\[c2|Error|error|Traceback" $S/out/cyber7/build.log | grep -v "pauldron ray" | tail -30
