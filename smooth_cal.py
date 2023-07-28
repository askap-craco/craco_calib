# normal python script - not command line executable
# make fitting for the bin file and return the results

import numpy as np  
import matplotlib.pyplot as plt

def _fit_value(val, x_ = None, deg=12):
    """
    Use polynomial fitting to fit values

    Parameters
    ----------
    val: array_like
        An array to be used in the fitting
    x_: array_like
        x values of the corresponding val, by default, will use np.arange function to create one
    deg: int
        degree of the polynomial in the fitting

    Returns
    ----------
    p_coef: np.array
        polynomial coefficients from the fitting
    """
    if x_ is None: x_ = np.arange(len(val))
    ### if there is nan data, flag it...
    x_ = x_[~np.isnan(val)]
    val = val[~np.isnan(val)]
    return np.polyfit(x_, val, deg=deg)

def _flag_bad(val, p_coef, x_=None, sigma=5):
    """
    flag outliers based on the fitting

    Parameters
    ----------
    val: array_like
        An array that was used in the fitting
    p_coef: np.array
        polynomial coefficients fitted from `_fit_value` function
    sigma: float
        threshold for determining outliers

    Returns
    ----------
    val: array_like
        An array with outliers replaced by np.nan
    """
    val = val.copy()
    p = np.poly1d(p_coef)
    if x_ is None: x_ = np.arange(len(val))
    res = val - p(x_)
    
    val[abs(res) > sigma * np.nanstd(res)] = np.nan
    return val

def fit_iter(val, x_=None, deg=12, sigma=3, loop=3):
    """
    iteratively fitting between x_ and val. with outliers flagged in each iteration

    Parameters
    ----------
    val: array-like
        An array to be used in the fitting
    x_: array_like
        x values of the corresponding val, by default, will use np.arange function to create one
    deg: int
        degree of the polynomial in the fitting
    sigma: float
        threshold for determining outliers
    loop: int
        number of iteration to be performed in the fitting

    Returns
    ----------
    coef: np.array
        polynomial coefficients from the final fitting
    val: np.array
        value array with the mask in the final iteration
    """
    for i in range(loop):
        coef = _fit_value(val, x_=x_, deg=deg)
        val = _flag_bad(val, coef, x_=x_, sigma=sigma)
    
    return coef, val


def unwrap_angles(angles, period=360):
    """
    un-wrap angles to make it possible to perform line fitting

    Parameters
    ----------
    angles: array-like
        a list of angle in order to be unwrapped
    period: float
        the period of the wrapping

    Returns
    ----------
    angles_: np.array
        unwrapped angles
    """
    angles_ = []
    previous=None
    for i in range(len(angles)):
        current = angles[i]
        if previous is None: 
            angles_.append(current)
        
        ### calculate the difference...
        else:
            dif = current - previous
            if abs(dif) > period / 4:
                angles_.append(current - np.round(dif / period) * period)
            else:
                angles_.append(current)

        ### assume no huge difference - but we can do a linear fit to predict...
        if not np.isnan(angles_[-1]): previous = angles_[-1]

    return np.array(angles_)

def wrap_angles(angles, period=360., bias=-180.):
    angles = np.array(angles)
    return angles % period + bias


### functions to actually do the fitting based on the calibration bin file
# basic idea: plot diagnostic plots and give a new bin file with smoothing
def _check_nan(arr):
    """
    check if the elements in an array are all nans

    Parameters
    ----------
    arr: array-like

    Returns
    ----------
    result: bool
        True if all elements are nan in the input array, else False
    """
    return (~np.isnan(arr)).sum() == 0

def _check_refant(bp, ia):
    """
    check if a given antenna is good to serve as a reference

    Parameters
    ----------
    bp: array-like
        bandpass solution from field calibration (four dimension)
    ia: int
        index of the antenna to check

    Retunrs
    ----------
    result: bool
        True if this antenna is good as a reference

    Notes
    ----------
    TODO: 
        check how many missing channels are there for this antenna,
        currently, we only check if all data for this antenna is empty...
    """
    bp_ant = bp[0, ia, ...]
    return not _check_nan(bp_ant)

def _smooth_amp_iter(bp_chan, deg=12, mask=None):
    """
    make fit of bandpass amplitude for a specific antenna, polarisation, and return the smoothed bandpass

    Parameters
    ----------
    bp_chan: array-like
        bandpass solution for a specific antenna, and a polarisation
        it should be a 1-D array, with the number of the element equals to nchan
    deg: int
        polynomial degree for the fitting
    mask: np.array
        numpy array of masks to mask out bad-behaved channels

    Return
    ----------
    p_coef: np.array
        polynomial coefficients
    bp_: np.array
        smoothed bandpass value
    bp_f: np.array
        input bandpass amplitude with mask
    """
    # create input data...
    bp_chan_amp = np.abs(bp_chan)
    if mask is not None: bp_chan_amp[mask] = np.nan
    if _check_nan(bp_chan_amp): return np.array([0]), bp_chan_amp, bp_chan_amp
    x_ = np.arange(bp_chan_amp.shape[0])

    # perform fitting
    coef, bp_f = fit_iter(bp_chan_amp, x_=None, deg=deg, sigma=3, loop=3)
    p_func = np.poly1d(coef)

    bp_ = p_func(x_)

    return coef, bp_, bp_f

def _smooth_amp(
        bp_chan, maxdeg=6, mask=None,
        deg_sigma=[
            (0, 6), (1, 5), (2, 5), (3, 5),
            (4, 3), (5, 3), (6, 3),
        ],
        loop=3,
    ):
    """
    make fit of bandpass amplitude for a specific antenna, polarisation, and return the smoothed bandpass

    Parameters
    ----------
    bp_chan: array-like
        bandpass solution for a specific antenna, and a polarisation
        it should be a 1-D array, with the number of the element equals to nchan
    maxdeg: int
        maximum polynomial degree for the fitting
    mask: np.array
        numpy array of masks to mask out bad-behaved channels
    deg_sigma: list of 2 elements tuples
        degree of polyniomial fitting and corresponding sigma to determine the outliers

    Return
    ----------
    p_coef: np.array
        polynomial coefficients
    bp_: np.array
        smoothed bandpass value
    bp_f: np.array
        input bandpass amplitude with mask
    """
    assert maxdeg+1 <= len(deg_sigma), "not enough sigma threshold found in `deg_sigma`"

    bp_chan_amp = np.abs(bp_chan)

    if mask is not None: bp_chan_amp[mask] = np.nan
    if _check_nan(bp_chan_amp): return np.array([0]), bp_chan_amp, bp_chan_amp
    x_ = np.arange(bp_chan_amp.shape[0])

    # perform fitting - for amplitude, don't do it in a regular iterative way
    _bp_chan_amp = bp_chan_amp.copy() # make a copy
    for deg, sigma in deg_sigma:
        if deg > maxdeg: continue
        for i in range(loop):
            # find out median here in the 0-th order
            if deg == 0:
                coef = np.array(np.nanmedian(_bp_chan_amp))
            else:
                coef = _fit_value(_bp_chan_amp, x_=x_, deg=deg)
            _bp_chan_amp = _flag_bad(_bp_chan_amp, coef, x_=x_, sigma=sigma)

    p_func = np.poly1d(coef)
    bp_ = p_func(x_)

    return coef, bp_, _bp_chan_amp

def _smooth_phase(bp_chan, bp_chan_ref, mask=None):
    """
    make bandpass phase fitting

    Parameters
    ----------
    bp_chan: array-like
        bandpass for a specific antenna and polarisation
        should be a 1D array, the number of element the same as nchan
    bp_chan_ref: array-like
        bandpass for a reference antenna
    mask: np.array
        numpy array of masks to mask out bad-behaved channels

    Returns
    ----------
    p_coef: np.array
        polynomial coefficients
    bp_: np.array
        smoothed bandpass value
    bp_f: np.array
        input bandpass phase with mask
    """
    bp_chan_phase = np.angle(bp_chan / bp_chan_ref) # in radian
    if mask is not None: bp_chan_phase[mask] = np.nan
    if _check_nan(bp_chan_phase): return np.array([0]), bp_chan_phase, bp_chan_phase
    x_ = np.arange(bp_chan_phase.shape[0])

    bp_chan_phase = unwrap_angles(bp_chan_phase, period=2*np.pi)

    coef, bp_f = fit_iter(bp_chan_phase, x_=x_, deg=1, sigma=3, loop=3)
    p_func = np.poly1d(coef)

    bp_ = p_func(x_)

    return coef, bp_, bp_f

def _select_refant(bp):
    """
    select reference antennas

    Parameters
    ---------
    bp: array-like
        4D solution array, with a shape of (n, nant, nchan, npol)
    
    Returns
    ----------
    ia: int
        index of the reference antenna
    """
    _, nant, _, _ = bp.shape
    for ia in range(nant):
        if _check_refant(bp, ia):
            return ia
    raise ValueError("No Reference antenna found...")

def plot_smooth_process(
    bp_chan, bp_chan_ref, amp_result, phase_result,
    color, axes=None, fig=None,
):
    """
    make diagnostic plots for smoothing process

    Parameters
    ----------
    bp_chan: np.array
        original bandpass for an antenna and a polarisation
    bp_chan_ref: np.array
        bandpass for reference antenna
    amp_result: tuple, three elements
        returned values from `_smooth_amp`
    phase_result: tuple, three elements
        returned values from `_smooth_phase`

    Returns
    ----------
    fig: mpl.figure.Figure
    axes: list, 2 element of mpl.axes._subplots.AxesSubplot
    """
    if axes is None:
        if fig is None:
            fig = plt.figure(figsize=(6, 8))
        axes = fig.subplots(2, 1)
    
    bp_chan_amp = np.abs(bp_chan)
    bp_chan_phase = unwrap_angles(np.angle(bp_chan/bp_chan_ref, deg=True))
    x_ = np.arange(bp_chan_amp.shape[0])
    ### plot amplitude
    axes[0].scatter(x_, bp_chan_amp, color=color, alpha=0.3, marker="x", s=20)
    axes[0].scatter(x_, amp_result[-1], color=color, s=8)
    axes[0].plot(x_, amp_result[1], color=color)
    axes[0].set_xlabel("channel #")
    axes[0].set_ylabel("amplitude gain")

    ### plot phase
    axes[1].scatter(x_, bp_chan_phase, color=color, alpha=0.3, marker="x", s=20)
    axes[1].scatter(x_, np.rad2deg(phase_result[-1]), color=color, s=8)
    axes[1].plot(x_, np.rad2deg(phase_result[1]), color=color)

    #axes[1].set_ylim(-200, 200)
    axes[1].set_xlabel("channel #")
    axes[1].set_ylabel("phase gain (deg)")

    return fig, axes


def smooth_bandpass(bp, amp_threshold=20., plot=True, plotdir="./"):
    """
    fit amplitude in the bandpass

    Parameters
    ----------
    bp: array-like, should be four dimension
        bandpass solution from either field calibration code or casa
        the dimension of the array should be (n, nant, nchan, npol)
    amp_threshold: float
        channels with amplitude greater than this threshold are considered as bad channels
    plot: bool
        True if plot diagnoistic plots

    Returns
    ----------
    bp_: np.array
        smoothed bandpass solution - the dimension is the same as the input array
    """
    # select reference antenna
    ia_ref = _select_refant(bp)
    print(ia_ref)

    bp_ = np.zeros(bp.shape, dtype=complex)
    n, nant, nchan, npol = bp.shape

    for i in range(n):
        for ia in range(nant):
            if plot:
                fig = plt.figure(figsize=(6, 8))
                axes = fig.subplots(2, 1)
            for ipol in range(npol):
                # for XY, YX, set it to nan for all
                if ipol == 1 or ipol == 2: 
                    bp_[i, ia, :, ipol] = np.nan + 1j * np.nan
                    continue
                bp_chan = bp[i, ia, :, ipol]
                # mask = np.abs(bp_chan) > 20.
                mask = None
                amp_coef, bp_amp_, bp_amp_f = _smooth_amp(bp_chan, maxdeg=0, mask=mask)
                phase_coef, bp_phase_, bp_phase_f = _smooth_phase(bp_chan, bp[i, ia_ref, :, ipol], mask=mask)

                ### make it to amp * np.exp(i*phase)
                bp_[i, ia, :, ipol] = bp_amp_ * np.exp(1j * bp_phase_)

                # do the plotting...
                if plot:
                    color = None
                    if ipol == 0: color="black"
                    if ipol == 3: color="red"

                    if color is not None:
                        fig, axes = plot_smooth_process(
                            bp_chan, bp[i, ia_ref, :, ipol],
                            (amp_coef, bp_amp_, bp_amp_f),
                            (phase_coef, bp_phase_, bp_phase_f),
                            color, axes=axes, fig=fig
                        )
            if plot:
                fig.savefig(f"{plotdir}/bp_ak{ia+1}.png", bbox_inches="tight")
                plt.close()

    return bp_


