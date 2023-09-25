# normal python script - not command line executable
# make fitting for the bin file and return the results

from craco import plotbp
from craft.cmdline import strrange
import numpy as np
import os

import matplotlib.pyplot as plt
from multiprocessing import Pool, cpu_count

import warnings
warnings.filterwarnings('ignore')

def count_nan(arr, isnan=True, fraction=True):
    """
    count how many nan or inf values are there in a given array
    
    Params
    ----------
    arr: numpy.ndarray
    isnan: bool, True by default
        return the number/fractional of nan value if True,
        otherwise return non-nan or non-inf values
    fraction: bool, True by default
        return the fractional of the value fulfilling the criteria if True
        otherwise return count
    """
    total = np.size(arr)
    nancount = (np.isnan(arr) | np.isinf(arr)).sum()
    
    if fraction:
        if isnan: return nancount / total
        return 1 - nancount / total
    if isnan: return nancount
    return total - nancount

class UnWrapFit:
    
    def __init__(
        self, yvalue, xvalue=None, 
        ktrials=None, period=2*np.pi,
        outlier_sigma=3, outlier_loop=3,
        fit_sigma = 3, fit_loop = 3,
    ):
        maximum_wrap = 8
        maximum_nx = 288
        ntrials = 500
        
        self.yvalue = np.array(yvalue)
        if xvalue is None:
            self.xvalue = np.arange(self.yvalue.shape[0])
        else:
            self.xvalue = np.array(xvalue)
            
        if ktrials is None:
            self.ktrials = np.linspace(
                -maximum_wrap*period/maximum_nx, 
                maximum_wrap*period/maximum_nx, 
                ntrials
            )
        else:
            self.ktrials = np.array(ktrials)
        
        self.period = period
            
        self.outlier_sigma = outlier_sigma
        self.outlier_loop = outlier_loop
        self.fit_sigma = fit_sigma
        self.fit_loop = fit_loop
            
    def _drop_outlier_wmedian(self, values, sigma=None, loop=None):
        """
        drop outlier values with regard to median values
        """
        if sigma is None: sigma = self.outlier_sigma
        if loop is None: loop = self.outlier_loop
            
        for i in range(loop):
            med = np.nanmedian(values)
            std = np.nanstd(values)
            values[abs(med - values) > sigma * std] = np.nan
        return values
    
    def _get_unwraplinefit_residual(
        self, slope, drop_residual_outlier=True,
    ):        
        yy = slope * self.xvalue
        res = (self.yvalue - yy) % self.period
        if drop_residual_outlier:
            res = self._drop_outlier_wmedian(res, sigma=self.outlier_sigma, loop=self.outlier_loop)
        return res
    
    def estimate_optimal_fit(self):
            
        stds_ktrails = np.array([
            np.nanstd(self._get_unwraplinefit_residual(k, ))
            for k in self.ktrials
        ])
        
        self.slopebest = self.ktrials[stds_ktrails.argmin()]
        self.interbest = np.nanmedian(self._get_unwraplinefit_residual(self.slopebest))
        

    
    def unwrap_data(self,):
        
        besty = self.slopebest * self.xvalue + self.interbest
        self.unwrapy = self.yvalue + np.rint((besty - self.yvalue) / self.period) * self.period
        
    
    def unwrap_poly_fit(self):
        xtofit = self.xvalue
        ytofit = self.unwrapy
        ### check if all ytofit is nan
        if (~np.isnan(ytofit)).sum() == 0:
            self.yfit = np.ones_like(xtofit) * np.nan
            return
        
        for i in range(self.fit_loop):
            nonbool = ~np.isnan(ytofit)
            xtofit = xtofit[nonbool]
            ytofit = ytofit[nonbool]
            
            pfit = np.poly1d(np.polyfit(xtofit, ytofit, deg=1))
            yfit = pfit(xtofit)
            
            # get residual etc.
            res = yfit - ytofit
            ytofit[abs(res) > self.fit_sigma * np.nanstd(res)] = np.nan

        self.yfit = pfit(self.xvalue)
        
    def run(self):
        self.estimate_optimal_fit()
        self.unwrap_data()
        self.unwrap_poly_fit()
        return self
    

class CracoBandPass:
    
    def __init__(self, fname, refant=None, flagchan=None):
        self.bandpass = self._load_bandpass(fname)
        self.bandpass = self._apply_flag(self.bandpass, flagchan)
        self.nant, self.nchan, self.npol = self.bandpass.shape # get the shape of the solution
        self.ira = self._check_refant(refant)
        
        ###
        self._load_amplitude()
        self._load_phase()
        
    
    def _load_bandpass(self, fname):
        """
        load the bandpass from different files to make sure that the output has the following shape
        (nant, nchan, npol)
        """
        if fname.endswith(".bin"): # bin file from Emil scripts
            bpcls = plotbp.Bandpass.load(fname)
            bp = bpcls.bandpass.copy()[0, ...]
            
            ### add some code here if you want to deal with different npol
            # nant, nchan, npol = bp.shape
            
            return bp
            
        raise ValueError("not supported file type...")
        
    def _apply_flag(self, bandpass, flagchan):
        """
        apply channel flags to the solution...
        """
        if flagchan is None: return bandpass # do not do any changes...
        if isinstance(flagchan, str):
            flagchan = strrange(flagchan)
        ### apply flags
        bandpass[:, flagchan, :] = np.nan + 1j * np.nan
        return bandpass
            
    def _check_refant(self, refant=None):
        if refant is None:
            valid_data_arr = np.array([count_nan(self.bandpass[ia, ...]) for ia in range(self.nant)])
            ira = valid_data_arr.argmin() # ref-antenna index, 0-indexed!
        else:
            ira = int(refant)
        assert valid_data_arr[ira] != 1., "no reference antenna found..."
        return ira
    
    def _amplitude_fit(self, y, sigma=3, loop=3):
        """
        fit a straight line...
        """
        for i in range(loop):
            ymedian = np.nanmedian(y)
            res = y - ymedian
            y[abs(res) > np.nanstd(res)] = np.nan
        return np.nanmedian(y)
    
    def _load_amplitude(self, ):
        """
        load amplitude into self.bpamp
        """
        self.bpamp = np.abs(self.bandpass)
        
    def _load_phase(self, ):
        """
        load relative degree into bp.bpphase
        """
        self.bpphase = np.angle(self.bandpass / self.bandpass[self.ira, ...])
    
    ### fit part
    def _smooth_sol_ant(self, ia, plot=True, plotdir="./bpsmooth"):
#         print(f"smoothing bandpass solution for antenna ak{ia+1}")
        
        bpantsmooth = np.zeros((self.nchan, self.npol), dtype=complex)
        
        if plot: 
            fig = plt.figure(figsize=(6, 8), facecolor="white")
            axes = fig.subplots(2, 1)
        
        for ipol in range(self.npol):
            if ipol == 1 or ipol == 2:
                bpantsmooth[:, ipol] = np.nan + 1j * np.nan
            else:
                smooth_amp = self._amplitude_fit(self.bpamp[ia, :, ipol])

                # fit phase
                phasefit = UnWrapFit(self.bpphase[ia, :, ipol]).run()
                smooth_phase = phasefit.yfit

                bpantsmooth[:, ipol] = smooth_amp * np.exp(1j * smooth_phase)
                
            if plot:
            #                 print(f"plotting ak{ia+1} for pol{ipol}")
                color = None
                if ipol == 0: color = "black"
                if ipol == 3: color = "red"

                if color is not None:
                    ### plot amplitude
                    axes[0].scatter(
                        np.arange(self.nchan), self.bpamp[ia, :, ipol],
                        color=color, alpha=0.5, marker="x", s=20,
                    )
                    axes[0].plot(np.arange(self.nchan), np.ones(self.nchan)*smooth_amp)
                    axes[0].set_xlabel("channel #")
                    axes[0].set_ylabel("gain amplitude")

                    ### plot phase
                    axes[1].scatter(
                        np.arange(self.nchan), np.rad2deg(self.bpphase[ia, :, ipol]),
                        color=color, alpha=0.3, marker="x", s=20,
                    )
                    axes[1].scatter(
                        np.arange(self.nchan), np.rad2deg(phasefit.unwrapy),
                        color=color, alpha=0.5, marker="x", s=20,
                    )
                    axes[1].plot(np.arange(self.nchan), np.rad2deg(smooth_phase))
                    axes[1].set_xlabel("channel #")
                    axes[1].set_ylabel("gain phase")
        if plot:
        #             print(f"saving solution for ak{ia+1}...")
            if not os.path.exists(plotdir):
                os.makedirs(plotdir)
            fig.savefig(f"{plotdir}/bp_ak{ia+1}.png", bbox_inches="tight")
            plt.close()
        
        return ia, bpantsmooth
        
    def smooth_sol(self, plot=True, plotdir="./bpsmooth", multiproc=False, ncpu=36):
        """
        smooth solution
        """
        bpsmooth = np.zeros((self.nant, self.nchan, self.npol), dtype=complex)
        
        if multiproc:
            print("not sure why this is not working...")
            raise NotImplementedError("MULTIPROCESSING NOT ALLOWED...")
            ncpu_max = cpu_count()
            if ncpu > ncpu_max: ncpu = ncpu_max
            
            pool = Pool(ncpu)
            results = pool.map(
                self._smooth_sol_ant,
                [
                    [ia, plot, plotdir] for ia in range(self.nant)
                ],
            )
            
            ### map the solution back
            for ia, bpantsmooth in results:
                bpsmooth[ia] = bpantsmooth
        
        if not multiproc:
            for ia in range(self.nant):
                ia, bpantsmooth = self._smooth_sol_ant(ia, plot=plot, plotdir=plotdir)
                bpsmooth[ia] = bpantsmooth
                plt.close()
                
        self.bpsmooth = bpsmooth.reshape((1, self.nant, self.nchan, self.npol))
        
    def dump_calibration(self, binname):
        ### add one dimension
        np.save(binname, self.bpsmooth)

