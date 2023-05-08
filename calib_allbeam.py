#!/usr/bin/env python
# python scripts for calibration for all beams
import os
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
    build_dir="/data/craco/wan342/scripts/craco_calib/scripts"
):
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
    os.system(f"gen_calibration_soln.py -vis_uvfits {work_dir}/{craco_fitsfname} -build_dir {build_dir}")

def _main():
    args = argparse.ArgumentParser()
    args.add_argument("-craco_input", type=str, help="path to the craco uvfits file")
    args.add_argument("-work_dir", type=str, help="directory for saving the final result")
    args.add_argument(
        "-build_dir", type=str, help="calibration binary files directory", 
        default="/data/craco/wan342/scripts/craco_calib/scripts"
    )

    values = args.parse_args()

    execute_calibration(values.craco_input, values.work_dir, values.build_dir)

if __name__ == "__main__":
    _main()