#This script makes images at timesteps and difference images to try to locate an FRB
#Built on scripts by Emil Lenc, adapted by Marcin Glowacki
#This assumes you have adapted flag.py with the antennas you want to flag!
#process_findfrb.sh target.ms hh:mm:ss xxhxxmxx xxdxxmxx FRBNAME False
#where first hh:mm:ss is time of FRB, within one second before said time
#next two the phasecentre if this wants to be updated. 
#next is time of FRB, then name of the FRB, and a True/False flag for it the FRB happened on the scond (UTC) day of the observation

target_ms=${1:-2021-08-07_102658_2.ms}
timeofFRB=${2:-15:48:09}
PC_RA=${3:-default}
PC_DEC=${4:-default}
FRBName=${5:-FRB200000}
secondday=${6:-False}


bandpass_bin=${target_ms/.ms/.bin}

#module loading prep for pawsey
module use /group/askap/chi139/modulefiles

#first, let's copy the files to the processing subdirectory
#and before that, we'll remove any .ms files already there
#and before that, check the directory exists!
mkdir -p processing/$FRBName/SELF/

rm -fr processing/$FRBName/SELF/*.ms
rm -fr processing/$FRBName/SELF/frbfield*
rm -fr processing/$FRBName/SELF/positions*

./skymodel_Cal.py $FRBName $target_ms

echo 'Applying solutions...'
applysolutions processing/$FRBName/SELF/$target_ms processing/$FRBName/SELF/$bandpass_bin

#flag
./flag.py processing/$FRBName/SELF/$target_ms

#rm -fr frb_*_15min*

#make the image, dirty and clean versions - takes time!!
#load it back up
module load casa-aces
echo 'Creating field images...'
casa --nologger -c frbfield_clean.py processing/$FRBName/SELF/$target_ms $PC_RA $PC_DEC $FRBName True
echo 'Source finding...'
casa --nologger -c find_sources.py processing/$FRBName/SELF/frbfield_n1e4_larger.fits $FRBName True

#copy results to output
cp -R processing/$FRBName/SELF/frbfield_n1e4_larger.fits output/${FRBName}_SELF_field_n1e4_larger.fits
cp -R processing/$FRBName/SELF/frbfield_dirty.fits output/${FRBName}_SELF_field_dirty.fits
cp -R processing/$FRBName/SELF/frbfield_n1e4.fits output/${FRBName}_SELF_field_n1e4.fits
cp -R processing/$FRBName/SELF/positions.txt output/${FRBName}_SELF_positions.txt
cp -R processing/$FRBName/SELF/positions_rad.txt output/${FRBName}_SELF_positions_rad.txt
cp -R processing/$FRBName/SELF/positions_pix.txt output/${FRBName}_SELF_positions_pix.txt

module unload casa-aces
#python positionconversion.py
