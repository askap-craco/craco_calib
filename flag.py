from casacore.tables import *
import argparse

def process(ms, flag_extremes = True):
    
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

def main(args):
    if args.vis is None:
        raise ValueError("Need to provide inp vis ms to process")
    else:
        ms = args.vis

    if args.flag_extremes.lower() in ['y', 'yes', 'true']:
        flag_extremes = True
    elif args.flag_extremes.lower() in ['n', 'no', 'false']:
        flag_extremes = False
    else:
        raise ValueError("Unexpected value for -flag_extremes flag: {0}".format(args.flag_extremes))
    process(ms, flag_extremes)

if __name__ == '__main__':
    a = argparse.ArgumentParser()
    a.add_argument("-vis", type=str, help="Input vis ms to flag")
    a.add_argument("-flag_extremes", type=str, help="Flag Extremes? (y/n) (def: y)", default="y")

    args = a.parse_args()
    main(args)


