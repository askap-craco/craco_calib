#!/usr/bin/env python

### python script for getting calibration solution for a beam
### this is designed for skadi cluster

import os
import re
import glob
import argparse

import logging
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def _check_file(file, dir):
    """
    check if a file is already in a given directory...
    """
    if file.endswith("/"): file = file[:-1]
    filebase = file.split("/")[-1]
    if os.path.exists(f"{dir}/{filebase}"):
        return True
    return False

# caveat: link the uvfits file to the correct location
class BeamCalibrator:
    def __init__(
        self, uvfitspath,
        caldir="/data/craco/craco/calibration", #="/CRACO/DATA_00/craco/calibration", # make it store in separate node
        build_dir="/CRACO/SOFTWARE/craco/wan342/Software/craco_calib/scripts",
        catalog="/CRACO/DATA_00/craco/calibration/data/racs-low.fits", 
        catfreq=887.5, overwrite=True
    ):
        self.uvfitspath = os.path.abspath(uvfitspath)
        self.caldir = caldir
        self.build_dir = build_dir
        self.catalog = catalog
        self.catfreq = catfreq
        self.overwrite = overwrite

        ### extract information based on uvfitspath
        self.obsinfo = self.extract_uvfits_info(self.uvfitspath)

    def extract_uvfits_info(self, uvfitspath):
        # change this function if file structure has been changed
        # currently it follows - SB054940/scans/00/20231124034717/b10.uvfits
        pattern = "SB(\d{6})/scans/(\d{2})/(\d{14})/b(\d{2})"
        log.info("extract observation information...")
        beaminfo = re.findall(pattern, uvfitspath)
        assert len(beaminfo) == 1, f"no beam information found in {uvfitspath}"
        beaminfo = beaminfo[0] # there should be only one matched info
        beaminfokeys = ["sbid", "scan", "tstart", "beam"]

        return {i:j for i, j in zip(beaminfokeys, beaminfo)}

    def __get_workdir(self, caldir, obsinfo):
        """
        construct working directory for this given observation
        """
        return f"""{caldir}/SB{obsinfo["sbid"]}/{obsinfo["beam"]}"""

    def prepare_calib(self, overwrite):
        """
        function to prepare for following calibration
        - check if there is folder created
        - check if there is solution existed
        - remove old files if solution existed and overwrite is True
        """
        self.workdir = self.__get_workdir(self.caldir, self.obsinfo)
        ### create new folders
        if not os.path.exists(self.workdir):
            os.makedirs(self.workdir)

        # check if b<beam>.aver.4pol.smooth.npy exists
        solfname = f"""b{self.obsinfo["beam"]}.aver.4pol.npy"""
        if _check_file(solfname, self.workdir):
            if not overwrite: # if solution exists and no overwrite, do nothing #here raise an error
                log.warning("file exists... no further action needed...")
                raise ValueError("calibration exists without overwriting... aborted...")

        ### clean up the directory
        rmcmd = f"rm -r {self.workdir}/*"
        log.info(f"clean up work directory with {rmcmd}")
        os.system(rmcmd)

        ### link uvfits file to the work directory
        lncmd = f"""ln -s {self.uvfitspath} {self.workdir}/b{self.obsinfo["beam"]}.uvfits"""
        log.info("make soft link of the uvfits file...")
        os.system(lncmd)

    def execute_calib(self, ):
        calcmd = f"""gen_calibration_soln.py -vis_uvfits {self.workdir}/b{self.obsinfo["beam"]}.uvfits"""
        calcmd += f""" -build_dir {self.build_dir} -catalog {self.catalog} -catfreq {self.catfreq}"""
        log.info(f"executing `gen_calibration_soln.py` command - {calcmd}")
        os.system(calcmd)

    def run(self, overwrite=True):
        self.prepare_calib(overwrite=overwrite)
        self.execute_calib()

def main():
    args = argparse.ArgumentParser()
    args.add_argument("-uv", "--uvfits", type=str, help="uvfits file to run calibration on")
    
    values = args.parse_args()

    beamcal = BeamCalibrator(uvfitspath=values.uvfits)
    beamcal.run(overwrite=True)


if __name__ == "__main__":
    main()





        
