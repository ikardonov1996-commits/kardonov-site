#!/bin/bash
# relaunch the robot-side final chain if it is not running (flock in the chain prevents duplicates)
S=/tmp/claude-0/-home-user-kardonov-site/cb30cd45-1b88-5b9b-b3ff-480343f6cfce/scratchpad; L=$S/out/hero/final_robot/final.log
grep -q ROWS_CHAIN_DONE $L 2>/dev/null && { echo CHAIN_DONE; exit 0; }
cd $S/out/hero; JOBS="E -45,A -37" setsid nohup $S/scripts/hero/run_rows_robot.sh > /dev/null 2>&1 < /dev/null &
