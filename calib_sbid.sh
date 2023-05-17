#!/usr/bin/bash
sbid=$1

# add LD_LIBRARY_PATH for this run
LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/data/big/craco/wan342/lib:/data/big/craco/wan342/software/anaconda/envs/calib/lib
PATH=$PATH:/data/big/craco/wan342/bin

/data/big/craco/wan342/craco_calib/calib_allbeam.py -s $sbid 

rm casa*.log