#This script makes images at timesteps and difference images to try to locate an FRB
#Built on scripts by Emil Lenc, adapted by Marcin Glowacki
#This assumes you have adapted flag.py with the antennas you want to flag!
#process_findfrb.sh bandpass.ms bandpass.model target.ms hh:mm:ss xxhxxmxx xxdxxmxx FRBNAME False
#where first hh:mm:ss is time of FRB, within one second before said time
#next two the phasecentre if this wants to be updated. 
#next is time of FRB, then name of the FRB, and a True/False flag for it the FRB happened on the scond (UTC) day of the observation

bandpass_ms=${1:-1934.SB30179.beam02.ms}
bandpass_model=${2:-1934-638.model}
target_ms=${3:-2021-08-07_102658_2.ms}
timeofFRB=${4:-15:48:09}
PC_RA=${5:-default}
PC_DEC=${6:-default}
FRBName=${7:-FRB200000}
secondday=${8:-False}


bandpass_bin=${bandpass_ms/.ms/.bin}

#module loading prep for pawsey
module use /group/askap/chi139/modulefiles

#first, let's copy the files to the processing subdirectory
#and before that, we'll remove any .ms files already there
#and before that, check the directory exists!
mkdir -p processing/$FRBName

rm -fr processing/$FRBName/*.ms
rm -fr processing/$FRBName/frbfield*
rm -fr processing/$FRBName/positions*

# Make a work copy of the ms to avoid making the original incompatible with ASKAPsoft
cp -R $bandpass_ms processing/$FRBName/$bandpass_ms 
cp -R $target_ms processing/$FRBName/$targetms

#Bandpass pointing correction and calibration
./fix_dir.py processing/$FRBName/$bandpass_ms #1934.SB30179.beam02.ms
calibrate -minuv 200.0 -m $bandpass_model processing/$FRBName/$bandpass_ms processing/$FRBName/$bandpass_bin

#splits uncalibrated target into smaller dataset(s)
#first, load casa...
module load casa-aces
echo 'Splitting target...'
casa --nologger -c split_targetfield.py processing/$FRBName/$target_ms $timeofFRB $FRBName $secondday
#./split_target.py $target_ms $timeofFRB
#unload casa so we can go to casa-core
module unload casa-aces

#fix direction, apply bandpass solutions, flag
./fix_dir.py processing/$FRBName/frbfield.ms
echo 'Applying solutions...'
applysolutions processing/$FRBName/frbfield.ms processing/$FRBName/$bandpass_bin

#flag
./flag.py processing/$FRBName/frbfield.ms

rm -fr frb_*_15min*

#make the image, dirty and clean versions - takes time!!
#load it back up
module load casa-aces
echo 'Creating field images...'
casa --nologger -c frbfield_clean.py processing/$FRBName/frbfield.ms $PC_RA $PC_DEC $FRBName
echo 'Source finding...'
casa --nologger -c find_sources.py processing/$FRBName/frbfield_n1e4_larger.fits $FRBName

#copy results to output
cp -R processing/$FRBName/frbfield_n1e4_larger.fits output/${FRBName}_field_n1e4_larger.fits
cp -R processing/$FRBName/frbfield_dirty.fits output/${FRBName}_field_dirty.fits
cp -R processing/$FRBName/frbfield_n1e4.fits output/${FRBName}_field_n1e4.fits
cp -R processing/$FRBName/positions.txt output/${FRBName}_positions.txt
cp -R processing/$FRBName/positions_rad.txt output/${FRBName}_positions_rad.txt
cp -R processing/$FRBName/positions_pix.txt output/${FRBName}_positions_pix.txt

module unload casa-aces
python positionconversion.py
