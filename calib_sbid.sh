#!/usr/bin/bash
sbid=$1
run=$2
#flagchan=$3

# add LD_LIBRARY_PATH for this run
# LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/data/seren-01/big/craco/wan342/lib:/data/seren-01/big/craco/wan342/software/anaconda/envs/calib/lib
LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/data/seren-01/fast/wan342/lib:/data/seren-01/fast/wan342/software/conda3/envs/craco_calib/lib
PATH=$PATH:/data/seren-01/big/craco/wan342/bin

if [ -z "$run" ]; then
   /data/big/craco/wan342/craco_calib/calib_allbeam.py -s $sbid #-flagchan $flagchan
else
    /data/big/craco/wan342/craco_calib/calib_allbeam.py -s $sbid -r $run #-flagchan $flagchan
fi


rm casa*.log