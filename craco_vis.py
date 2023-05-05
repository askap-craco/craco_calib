### get basic information for CRACO visibility data (without loading all blocks)

from astropy.io import fits
from casacore import tables
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
    

    



