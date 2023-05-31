# craco_calib (PIPE)

This code is used for creating calibration solution for a given SBID on seren

### Usage
1. Load calib conda enviornment

   > conda activate calib
   
   Emil's script for the field calibration need the dependence on a range of libraries. We install that with conda
2. Cd to the script directory

   > cd /data/big/craco/calibration/scripts
   
   Two scripts are used in the whole process - `fixuvfits_sbid.sh` and `calib_sbid.sh`. They are under `/data/big/craco/calibration/scripts`
   
3. Fix uvfits files

   > ./fixuvfits_sbid.sh $SCHEDULE_BLOCK_ID
   
   Some uvfits files may not be closed correctly during the mpipipeline run, fix all uvfits files within a given SBID

4. Calibrate all beams for a given SBID

   > ./calib_sbid.sh $SCHEDULE_BLOCK_ID $RUNNAME

  This is the main part of the calibration, it will look for all uvfits file within a given SBID, do the calibration for all scans, all beams.
  If $RUNNAME is not specified, it will use `results` by default. That is the folder name where you store all the outputs.
  
  
### Result
All calibration solutions are stored under `/data/big/craco/calibration` by default. 
The path to the solution files follow the same rule as that for ccapfits files and uvfits files
For example, solution under `/data/big/craco/calibration/SB049120/scans/00/20230406114010/00` means that
this is the calibration file derivated from the observation SB49120, scan 00 (started on 2023-Apr-06 11:40:10), for beam 00.

For the most updated script, after running `calib_sbid.sh` script, there will be 5 files and 1 folder there
- `b??.aver.4pol.bin`: original `.bin` written by Emil's script
- `b??.aver.4pol.freq.npy`: frequency information from the calibration, this is loaded automatically when using `craco.calibration.load_gains` function
- `b??.aver.4pol.model`: sky model file, not useful in further steps
- `b??.aver.4pol.smooth.npy`: smoothed bandpass (i.e., fitting) from the original `.bin` file
- `b??.uvfits`: a symbolic link to the raw uvfits data, not useful in further steps
- `bp_smooth`: folder to store diagnostic plots when doing the smoothing (there are plots for each antenna separately)

Note: When loading, both `.bin` and `.smooth.npy` solutions need their corresponding `.freq.npy` file, don't forget that when copying across
   
   
