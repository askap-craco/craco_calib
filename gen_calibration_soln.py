#!/usr/bin/env python

import argparse, os
import numpy as np

from casatasks import importuvfits
from average_the_ms import process as average
from convert import process as convert
from extract_model_for_ms import process as extract
from flag import process as flag
from craco_vis import SimpleMeasurementSet
from smooth_cal import smooth_bandpass

### craco related
from craco import plotbp

def _load_binsol(binfile):
    """
    load bin calibration solution from `binfile`
    """
    bp = plotbp.Bandpass.load(binfile)
    return bp.bandpass.copy()

from carco_vis import SimpleMeasurementSet

def main(args):
    if args.vis_ms:
        inp_vis = args.vis_ms
    elif args.vis_uvfits:
        inp_vis = args.vis_uvfits.strip("uvfits") + "ms"
        print("------> Convering UV Fits ({0}) to MS ({1})".format(args.vis_uvfits, inp_vis))
        importuvfits(fitsfile=args.vis_uvfits, vis=inp_vis)

    if inp_vis.endswith("/"): inp_vis=inp_vis[:-1]
    work_dir = "/".join(inp_vis.split("/")[:-1])

    averaged_vis = inp_vis.strip("ms") + "aver.ms"
    print("------> Averaging MS ({0}) and saving to {1}".format(inp_vis, averaged_vis))

    average(inp_vis, averaged_vis, timebin="10s", freqbin=1) # average it to 1 MHz

    four_pol_vis = averaged_vis.strip("ms") + "4pol.ms"

    print("------> Converting MS ({0}) to 4pol ({1})".format(averaged_vis, four_pol_vis))
    convert(averaged_vis, four_pol_vis)

    model_name = four_pol_vis.strip("ms") + "model"
    print("------> Extracting sky model and saving to {0}".format(model_name))
    extract(
        four_pol_vis, pb_radii = 2.0, flux_cutoff = 0.005, spectral_index = -0.83,
        catalog_file=args.catalog, freq_cat=args.catfreq*1e6,
    )

    bin_name = four_pol_vis.strip("ms") + "bin"
    calibrate_cmd = "{build_dir}/calibrate -minuv 200.0 -m {model} {vis} {bin_name}".format(model=model_name, vis=four_pol_vis, build_dir=args.build_dir, bin_name=bin_name)
    print("------> Calibrating using the sky model and saving soln to {0}\n------> Executing {1}".format(bin_name, calibrate_cmd))
    os.system(calibrate_cmd)

    print("------> Exporting frequency from measurement sets....")
    craco_ms = SimpleMeasurementSet(four_pol_vis)
    freq_name = four_pol_vis.replace(".ms", ".freq.npy")
    np.save(freq_name, craco_ms.freqs)

    print("------> Fitting calibration solution...")
    bp = _load_binsol(bin_name)
    plotdir = f"{work_dir}/bp_smooth/"
    if not os.path.exists(plotdir): os.makedirs(plotdir)
    bp_ = smooth_bandpass(bp, plotdir=plotdir)
    smooth_npy = bin_name.strip("bin") + "smooth.npy"
    np.save(smooth_npy, bp_)
    
    if args.clean:
        print("------> Cleaning the directory....")
        work_dir = os.path.dirname(bin_name)
        os.system(f"rm -r {work_dir}/*.ms")
        

    print("-------> All Done!  We can now apply the solution saved in the soln file - {0}".format(bin_name))

if __name__ == '__main__':
    a = argparse.ArgumentParser()
    group = a.add_mutually_exclusive_group()
    group.add_argument("-vis_ms", type=str, help="Path to visibility ms file")
    group.add_argument("-vis_uvfits", type=str, help="Path to visibility UVFits file")

    ### remove measurement sets...
    a.add_argument(
        "-clean", type=bool, help="Clean the solution directory (i.e., remove all measurement sets)"
        default=True
    )
    
    a.add_argument(
        "-build_dir", type=str, help="Path to the build directory where the compiled scripts are kept", 
        default="/home/gup037/Codes/CRACO_calib/scripts/"
    )
    a.add_argument(
        "-catalog", type=str, help="Path to the catalogue used in self-calibration",
        default="/data/craco/wan342/data/catalogue/racs-low.fits"
    )
    a.add_argument(
        "-catfreq", type=float, help="central frequency of the catalogue provided",
        default=887.5
    )

    args = a.parse_args()
    main(args)

