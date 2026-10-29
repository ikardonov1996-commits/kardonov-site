S=/tmp/claude-0/-home-user-kardonov-site/cb30cd45-1b88-5b9b-b3ff-480343f6cfce/scratchpad
cd $S/out/cyber
/opt/blender/blender-4.2.3-linux-x64/blender -b stage_cut.blend -P $S/scripts/c6/skel_overlay.py -P $S/scripts/c6/ortho.py -- $S/out/cyber6/an/sk ArmRef,SK -0.157,-0.007,0.465,0.10 -Y,-X,+Y,+X MAT > /dev/null 2>&1
python3 $S/scripts/c6/grid.py $S/out/cyber6/an/sk -0.157,-0.007,0.465,0.10 $S/out/cyber6/an/sk_grid.png
