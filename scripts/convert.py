#!/usr/bin/env python

import os
import sys
import glob
from casacore.tables import *
import numpy as np

def make_4pol(t, column, zero=False):
    print("Expanding %s" %(column))
    # Rename the original column
    column_cp = "%s_OLD" %(column)
    t.renamecol(column, column_cp)
    # Get descriptions of the original column
    coldmi = t.getdminfo(column_cp)
    colddesc = t.coldesc(column_cp)
    # Prepare the updated column
    coldmi['NAME'] = column
    # Get a cell from the source to work out the approxiate dimensions
    cell = t.getcell(column_cp, 0)
    # How many polarisations?
    in_pol = cell.shape[-1]
    # Make space for all polarisations
    if in_pol == 2:
        out_cell = np.concatenate([cell,cell], axis=len(cell.shape)-1)
    elif in_pol == 1:
        out_cell = np.concatenate([cell,cell,cell,cell], axis=len(cell.shape)-1)
    # Get the new shape of the cell
    out_shape = out_cell.shape
    # Add the updated column
    if column == "FLAG_CATEGORY":
        kw = {}
        kw['CATEGORY'] = ['FLAG_CMD', 'ORIGINAL', 'USER']
        t.addcols(maketabdesc(makearrcoldesc(column, 0., valuetype=colddesc['desc']["valueType"], shape=out_shape, options=4, keywords=kw)), coldmi)
    else:
        t.addcols(maketabdesc(makearrcoldesc(column, 0., valuetype=colddesc['desc']["valueType"], shape=out_shape)), coldmi)
        
    # Get the original data
    msdata = t.getcol(column_cp)
    # Create the new column data by copying polarisation data
    if in_pol == 2:
        msdata2 = np.concatenate([msdata,msdata], axis=len(out_shape))
    elif in_pol == 1:
        msdata2 = np.concatenate([msdata,msdata,msdata,msdata], axis=len(out_shape))
    # Check if data needs to be zeroed
    if zero:
        msdata2[:,:,1] -= msdata2[:,:,1]
        msdata2[:,:,2] -= msdata2[:,:,2]
    # Save the new column data
    t.putcol(column, msdata2)
    # Remove the old column
    t.removecols([column_cp])
    return

def update_pol(ms):
    t = table("%s/POLARIZATION" %(ms), readonly=False)
    ct = t.getcol("CORR_TYPE")
    newct = np.array([[9, 10, 11, 12]])
    t.putcol("CORR_TYPE", newct)
    cp = t.getcol("CORR_PRODUCT")
    newcp = np.array([[[0,0,1,1],[0,1,0,1]]])
    t.putcol("CORR_PRODUCT", newcp)
    nc = t.getcol("NUM_CORR")
    nc[0] = 4
    t.putcol("NUM_CORR", 4)
    return

# Convert a casa averaged MS from 1/2 pol to 4 pol
ms = sys.argv[1] #"SB42431_tscrunch_v6_aver.ms"
msout = sys.argv[2] #"SB42431_tscrunch_v6_aver_4pol.ms"
os.system("rm -fr %s" %(msout))
os.system("cp -R %s %s" %(ms, msout))

t = table(msout, readonly=False)

make_4pol(t, "FLAG", False)
#make_4pol(t, "FLAG_CATEGORY", False)
make_4pol(t, "WEIGHT", False)
make_4pol(t, "SIGMA", False)
make_4pol(t, "DATA", True)
make_4pol(t, "WEIGHT_SPECTRUM", False)
make_4pol(t, "SIGMA_SPECTRUM", False)
t.close()
update_pol(msout)
