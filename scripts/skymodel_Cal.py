#!/usr/bin/env python

#script to apply sky model to a given ms (and also given SBID)
#VERY LARGELY BY EMIL LENC
#SLIGHTLY ADAPTED by Marcin Glowacki for case you have the data already rather than grabbing from RACS
import numpy as np
from casacore.tables import *
import matplotlib.pyplot as plt
import sys
import os
import glob

class Bandpass:
    def __init__(self):
        """Initialises parameters for reading a bandpass table
        """
        self.nsol = None
        self.nant = None
        self.npol = None
        self.nchan = None
        self.bandpass = None

    def load(self, filename):
        dt = np.dtype('<i4')
        fp = open(filename,'r')
        header = np.fromfile(fp, dtype=dt, count=2)
        headerValues = np.fromfile(fp, dtype=dt, count=10)
        self.nsol = headerValues[2]
        self.nant = headerValues[3]
        self.nchan = headerValues[4]
        self.npol = headerValues[5]
        self.bandpass = np.zeros((self.nsol, self.nant, self.nchan, self.npol), dtype=np.complex)
        dtc = np.dtype('<c16')
        self.bandpass = np.array(np.fromfile(fp, dtype=dtc, count=self.nsol * self.nant * self.nchan * self.npol))
        self.bandpass = self.bandpass.reshape((self.nsol, self.nant, self.nchan, self.npol))
        self.bandpass = np.sqrt(2.0) / self.bandpass
        fp.close()
        print("Read bandpass: %d solutions, %d antennas, %d channels, %d polarisations" %(self.nsol, self.nant, self.nchan, self.npol))

    def plotGains(self, sol, ref_ant = -1, outFile = None):
        fig = plt.figure(figsize=(14, 14))
        ant = 0
        max_val = 20.0

        amplitudes = np.abs(self.bandpass[sol])# / np.sqrt(2.0)
#        amplitudes[np.where(amplitudes>2.0)] = 0.0
        if ref_ant == -1:
            for ref in range(36):
                amps = (amplitudes[ref,:,0] + amplitudes[ref,:,3]) / 2.0
                good = amps[np.where(amps<max_val)]
                if len(good) > 0:
                    ref_ant = ref
                    break    
        print("Using ak%02d as reference" %(ref_ant + 1))
        self.bandpass[sol] = self.bandpass[sol] / self.bandpass[sol,ref_ant,:,:]
        phases = np.angle(self.bandpass[sol], deg=True)
#        phases[np.where(amplitudes==0.0)] = 0.0
        channels = np.array(range(self.nchan))
        NY = 6
        NX = 6
        lw = 0.5
        for y in range(NY):
            for x in range(NX):
                amps_xx = amplitudes[ant,:,0]
                amps_yy = amplitudes[ant,:,3]
                good_xx = amps_xx[np.where(amps_xx<max_val)]
                good_yy = amps_yy[np.where(amps_yy<max_val)]
                if len(good_xx) > 0 and len(good_yy) > 0:
                    plt.subplot(NY*2, NX, y * 2 * NX + x + 1)
                    plt.title("ak%02d" %(ant+1), fontsize=8)
                    plt.plot(channels, amplitudes[ant,:,0], marker=None, color="black", linewidth=lw)
                    plt.plot(channels, amplitudes[ant,:,3], marker=None, color="red", linewidth=lw)
                    plt.ylim(0.0, max_val)
                    # Plot phase
                    plt.subplot(NY*2, NX, y * 2 * NX + x + NX + 1) # maybe NY+1 instead of NX+1
                    plt.plot(channels, phases[ant,:,0], marker=None, color="black", linewidth=lw)
                    plt.plot(channels, phases[ant,:,3], marker=None, color="red", linewidth=lw)
                    plt.ylim(-200.0, 200.0)
                ant += 1

        plt.tight_layout()
        if outFile == None:
            plt.show()
        else:
            plt.savefig(outFile, dpi=300)
        plt.close()

def flag(ms, threshold = 200.0):
   t = table(ms, readonly=False)

   tf = table("%s/SPECTRAL_WINDOW" %(ms))
   ta = table("%s/ANTENNA" %(ms))
   nant = len(ta)
   nbl = int((nant / 2) * (nant - 1))

   print("Flagging autos")
   t1 = taql("select from $t where sumsqr(UVW[:2])<1.0")
   fdata = t1.getcol("FLAG")
   print(fdata.shape)
   fdata[:,:,:] = True
   t1.putcol("FLAG", fdata)
   t1.close()

   # Select only non-autos
   t1 = taql("select from $t where ANTENNA1 != ANTENNA2")

   cdata = t1.getcol("DATA")
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

   print("Flagging zeroed data")
   # Flag zeroed data
   zdata = np.where(cdata == 0.0+0.0j)
   fdata[zdata] = True

   print("Flagging extremes")
   #dxy = np.abs(cdata[:,:,1]-cdata[:,:,2])
   #bad_xy = np.where(dxy > threshold)
   #fdata[:,:,0][bad_xy] = True
   #fdata[:,:,1][bad_xy] = True
   #fdata[:,:,2][bad_xy] = True
   #fdata[:,:,3][bad_xy] = True

   t1.putcol("FLAG", fdata)
   t1.close()

   t.close()

FRBName = sys.argv[1]
#beam = int(sys.argv[2])
ms = sys.argv[2] #assuming it is beam specific
ref_ant = 3
#don't need source as we cannot access that!
#source = "/askapbuffer/scott/askap-scheduling-blocks"
cwd = os.getcwd()
print("Processing FRB %s, measurement %s" %(FRBName, ms))

# Find the original bandpass-calibrated data for the specified beam
#ms = glob.glob("%s/%s/*_%d.ms" %(source, sbid, beam))[0]
base_name = ms.split("/")[-1].replace(".ms", "")
#base_name = "%s_%02d" %(sbid, beam)
print(base_name)
#print("Processing %s" %(base_name))
#print("Measurementset: %s" %(ms))

# This is where the local sky model will be made and associated phase-selfcal performed.
work_path = "%s/processing/%s/SELF/" %(cwd, FRBName)

# Ensure the path exists
os.system("mkdir -p %s" %(work_path))
os.chdir(work_path)
#print(base_name,work_path)
# Remove any old temporary files from previous processing run
#os.system("rm -fr %s*" %(base_name))

# Make a work copy of the ms to avoid making the original incompatible with ASKAPsoft
os.system("cp -R %s/%s %s.ms" %(cwd, ms, base_name))
print('COPIED SUCCESSFULLY')
# Updated the field direction so that non-ASKAPsoft tools can work with the ms
os.system("%s/./fix_dir.py %s.ms" %(cwd, base_name))

#flag("%s.ms" %(base_name))

# Extract a local sky model for the ms
os.system("%s/./extract_model_for_ms.py %s.ms 3.0 0.01" %(cwd, base_name))

# Run bandpass calibration against RACS sky model
#os.system("/group/askap/glo049/src/calibrate_emil/calibrate -minuv 200.0 -m %s.model %s.ms %s.bin" %(base_name, base_name, base_name))
os.system("calibrate -minuv 200.0 -m %s.model %s.ms %s.bin" %(base_name, base_name, base_name))

# Plot bandpass solution
bp = Bandpass()
bp.load("%s.bin" %(base_name))
bp.plotGains(0, -1, "%s.png" %(base_name))

