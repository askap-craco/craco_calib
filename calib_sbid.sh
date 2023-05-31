#!/usr/bin/bash
sbid=$1
run=$2

# add LD_LIBRARY_PATH for this run
LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/data/seren-01/big/craco/wan342/lib:/data/seren-01/big/craco/wan342/software/anaconda/envs/calib/lib
PATH=$PATH:/data/seren-01/big/craco/wan342/bin

if [ -z "$run" ]; then
   /data/big/craco/wan342/craco_calib/calib_allbeam.py -s $sbid 
else
    /data/big/craco/wan342/craco_calib/calib_allbeam.py -s $sbid -r $run
fi


rm casa*.log