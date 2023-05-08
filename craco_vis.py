### get basic information for CRACO visibility data (without loading all blocks)

from astropy.io import fits
from casacore import tables
import numpy as np

from craco import plotbp

import warnings

class SimpleUvFits():

    def __init__(self, uvfits, ):
        self.hdul = self._load_fits(uvfits)

    def _load_fits(self, uvfits):
        """
        load fits file to hdulist
        """
        return fits.open(uvfits)

    @property
    def tsamp(self):
        data = self.hdul[0].data[0] # only take the first block
        try: ts = data["INTTIM"] # seconds
        except KeyError: ts = 0. # assume that nothing...
        return ts

    @property
    def foff(self):
        return self.hdul[0].header["CDELT4"]


class SimpleMeasurementSet():

    def __init__(self, vistab):
        # do some cleaning...
        if vistab.endswith("/"): vistab = vistab[:-1]

        self.dattab = self._load_data(vistab) 
        self.freqtab = self._load_freq(vistab)

        ### as we may need to change polarisation, don't use property to do that...
        self.npol = self.dattab.getcell("DATA", 0).shape[-1]


    def _load_data(self, vistab):
        return tables.table(vistab)

    def _load_freq(self, vistab):
        return tables.table("{}::SPECTRAL_WINDOW".format(vistab))

    @property
    def tsamp(self):
        return self.dattab.getcell("EXPOSURE", 0)

    @property
    def foff(self):
        return self.freqtab.getcell("CHAN_WIDTH", 0)[0]

    @property
    def freqs(self):
        """
        list of frequencies...
        """
        return self.freqtab.getcol("CHAN_FREQ")[0]

    @property
    def nant(self):
        """
        get the number of antennas
        """
        return np.unique(self.dattab.getcol("ANTENNA1")).shape[0]

    @property
    def nbl(self):
        return self.nant * (self.nant + 1) // 2

    # @property
    # def npol(self):
    #     return self.dattab.getcell("DATA", 0).shape[-1]

    @property
    def nchan(self):
        return self.dattab.getcell("DATA", 0).shape[0]

    @property
    def nt(self):
        return np.unique(self.dattab.getcol("TIME")).shape[0]

    ### load data... this can be super slow...
    def load_vis(self):
        self.vis = self.dattab.getcol("DATA").reshape(
            self.nt, self.nbl, self.nchan, self.npol
        )

        # if npol is 4, only select XX, YY
        if self.npol == 4:
            self.vis = self.vis[..., (0, 3)]
            self.npol = 2

        self.blant = self._load_bl_ant()

    def _load_bl_ant(self):
        """
        load antenna pairs as a numpy array, antennas are zero-based
        """
        return np.array([
            (i, j) for i in range(self.nant) for j in range(i, self.nant)
        ])

    def _load_gain(self, cal):
        """
        simple gain loader, as we will apply it to the original dataset,
        we don't consider frequency here
        """
        if cal.endswith(".bin"): # bin file
            g = plotbp.Bandpass.load(cal).copy()[0]
        elif cal.endswith(".smooth.npy"): # smoothed solution
            g = np.load(cal)[0]

        nant, nchan, npol = g.shape
        assert self.nant <= nant, "not enough antenna in the solution table..."
        assert self.nchan == nchan, "not equal number of channels in the solution table..."
        if npol == 4: g = g[..., (0, 3)]; npol = 2
        if npol == 2 and self.npol == 1:
            g = g.mean(axis=-1, keepdims=True)
        g = g[:self.nant, ...]

        ### load it to baseline based
        nant, nchan, npol = g.shape # reload npol...
        solarr = np.zeros(
            (self.nbl, self.nchan, self.npol),
            dtype=complex,
        )
        for ibl, antpair in enumerate(self.blant):
            ia1, ia2 = antpair
            s1 = g[ia1, ...]
            s2 = g[ia2, ...]
            p = s1 * np.conj(s2)
            solarr[ibl, ...] = p[:]

        return 1./solarr

    def apply_cal(self, cal):
        solarr = self._load_gain(cal) # load solution table - (nbl, nchan, npol)
        ### npol can be 1, 2
        self.calvis = self.vis * solarr[None, ...]



    



