#!/usr/bin/env python

import os
import sys
import glob
from casacore.tables import *

ms = sys.argv[1]
flag_extremes = True

t = table(ms, readonly=False)

tf = table("%s/SPECTRAL_WINDOW" %(ms))
ta = table("%s/ANTENNA" %(ms))
nant = len(ta)
nbl = int((nant / 2) * (nant - 1))

print("Flagging autos")
t1 = taql("select from $t where sumsqr(UVW[:2])<1.0")
fdata = t1.getcol("FLAG")
fdata[:,:,:] = True
t1.putcol("FLAG", fdata)
t1.close()

# Select only non-autos
t1 = taql("select from $t where ANTENNA1 != ANTENNA2")

cdata = t1.getcol("CORRECTED_DATA")
fdata = t1.getcol("FLAG")

nvis = fdata.shape[0]
nchan = fdata.shape[1]
npol = fdata.shape[2]
nint = int(nvis / nbl)

print("Antennas: %d" %(nant))
print("Baselines: %d" %(nbl))
print("Visibilities: %d" %(nvis))
print("Integrations: %d" %(nint))
print("Channels: %d" %(nchan))
print("Polarisations: %d\n" %(npol))

print("Flagging NaNs")
# Flag any NaNs
bad = np.where(np.isnan(cdata))
fdata[bad] = True

#print("Flagging extremes")

if flag_extremes:
    dxy = np.abs(cdata[:,:,0]-cdata[:,:,npol-1])
    bad_xy = np.where(dxy > 8.0)
    for pol in range(npol):
        fdata[:,:,pol][bad_xy] = True
    dxy = np.abs(cdata[:,:,0]-cdata[:,:,npol-1])
    bad_xx = np.where(cdata[:,:,0] == 0.0)
    for pol in range(npol):
        fdata[:,:,pol][bad_xx] = True
    bad_yy = np.where(cdata[:,:,0] == 0.0)
    for pol in range(npol):
        fdata[:,:,pol][bad_yy] = True

t1.putcol("FLAG", fdata)
t1.close()

t.close()
