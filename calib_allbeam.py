#!/usr/bin/env python
# python scripts for calibration for all beams
import os
import glob
import argparse

def _check_file(file, dir):
    """
    check if a file is already in a given directory...
    """
    if file.endswith("/"): file = file[:-1]
    filebase = file.split("/")[-1]
    if os.path.exists(f"{dir}/{filebase}"):
        return True
    return False

def execute_calibration(
    craco_input, work_dir="./",
    build_dir="/data/craco/wan342/scripts/craco_calib/scripts",
    catalog="racs-low.fits", catfreq=887.5,
):
# TODO: change catalog, build_dir, catfreq when moving to seren...
    """
    execute calibration process and save the output to a specific directory...
    """
    if craco_input is None:
        raise ValueError("no craco uvfits file found... use -h flag to see all available parameter")
    craco_fitsfname = os.path.basename(craco_input)
    # make new directory for `work_dir`
    if not os.path.exists(work_dir):
        os.makedirs(work_dir)
    # make symbolic link for measurement sets...
    if not _check_file(craco_input, work_dir):
        craco_input_abspath = os.path.abspath(craco_input)
        os.system(f"ln -s {craco_input_abspath} {work_dir}")

    # start to execute gen_calibration_soln...
    calcmd = f"gen_calibration_soln.py -vis_uvfits {work_dir}/{craco_fitsfname} -build_dir {build_dir}"
    calcmd += f" -catalog {catalog} -catfreq {catfreq}"
    os.system(calcmd)


### functions for running one SBID as a whole
def _find_uvfits(sbid):
    """
    find all uvfits files for a given sbid

    file pattern: /data/seren-01/big/craco/SB049721/scans/00/20230427155734/results/b00.uvfits
    """
    sbid = "SB{:0>6}".format(sbid)
    return glob.glob(f"/data/seren-*/big/craco/{sbid}/scans/*/*/results/b??.uvfits")

def _extract_uvfits_info(path):
    """
    extract uvfits information e.g., sbid, scan, starttime, beam, from the path

    Params
    ----------
    path: str
        path to the original uvfits file on seren
    
    Returns
    ----------
    fits_info: dict
        fits information, keys - ["sbid", "scan", "timestamp", "beam"]

    Note
    ----------
    given that the path is from `_find_uvfits` function, we will not regular expression to do that

    """
    subdir = path.split("/")

    fits_info = {
        "sbid": subdir[-6],
        "scan": subdir[-4],
        "timestamp": subdir[-3],
        "beam": subdir[-1][1:3],
    }

    return fits_info
    
def _construct_workdir(path, basedir="./"):
    """
    construct the working directory based on the path to the uvfits
    """
    finfo = _extract_uvfits_info(path)
    return f'''{basedir}/{finfo["sbid"]}/scans/{finfo["scan"]}/{finfo["timestamp"]}/{finfo["beam"]}/'''

def calibrate_sbid(
        sbid, basedir="./", build_dir="/data/craco/wan342/scripts/craco_calib/scripts",
        catalog="racs-low.fits", catfreq=887.5
    ):
    """
    produce calibration solution based on a given sbid.
    All relevant outputs are saving under the given base directory
    """
    uvfitspaths = _find_uvfits(sbid)
    for uvfitspath in uvfitspaths:
        work_dir = _construct_workdir(uvfitspath, basedir=basedir)
        execute_calibration(
            craco_input=uvfitspath,
            build_dir=build_dir,
            catalog=catalog, catfreq=catfreq,
        )

def _main():
    args = argparse.ArgumentParser()
    args.add_argument("-s", "--sbid", type=str, help="sbid (without letter SB)")
    args.add_argument(
        "-d", "--dir", type=str, help="base directory to save the output results"
        
    )
    args.add_argument(
        "-build_dir", type=str, help="calibration binary files directory", 
        default="/data/craco/wan342/scripts/craco_calib/scripts"
    )

    values = args.parse_args()

    execute_calibration(values.craco_input, values.work_dir, values.build_dir)

if __name__ == "__main__":
    _main()