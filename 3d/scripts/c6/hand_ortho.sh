S=/tmp/claude-0/-home-user-kardonov-site/cb30cd45-1b88-5b9b-b3ff-480343f6cfce/scratchpad
cd $S/out/cyber6
/opt/blender/blender-4.2.3-linux-x64/blender -b ${2:-build6.blend} -P $S/scripts/c6/ghost.py -P $S/scripts/c6/ortho.py -- $S/out/cyber6/an/$1 ${3:-Robo_Hand,Robo_WristJoint,Robo_HandTendon,ArmRef} -0.160,-0.004,0.460,0.12 -Y,-X,+Y,+X MAT > /dev/null 2>&1
python3 $S/scripts/c6/grid.py $S/out/cyber6/an/$1 -0.160,-0.004,0.460,0.12 $S/out/cyber6/an/$1_grid.png
