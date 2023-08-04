
import numpy as np
from astropy.coordinates import Angle, SkyCoord
from astropy import units as au
from astropy.table import Table
from casacore.tables import *
import argparse


class GaussianPB:
    
    def __init__(self,aperture = 12.0, expscaling = 4.0 * np.log(2.0), frequency = 1.1e9):
        
        self.aperture = aperture
        self.expScaling = expscaling
        self.frequency=frequency
        self.setXwidth(self.getFWHM())
        self.setYwidth(self.getFWHM())
        self.setAlpha(0.0)
        self.setXoff(0.0)
        self.setYoff(0.0)
        
    
    def getFWHM(self):
        sol = 299792458.0;
        fwhm = sol / self.frequency / self.aperture
        return fwhm
    
    def evaluate(self,offset = 0.0, freq = 0.0):
        if (freq > 0):
            self.frequency=freq
            
        pb = np.exp(-offset * offset * self.expScaling / (self.getFWHM() * self.getFWHM()))
        return pb
    
    def setXwidth(self,xwidth):
        self.xwidth = xwidth
        
    def setYwidth(self,ywidth):
        self.ywidth = ywidth
        
    def setAlpha(self,Angle):
        self.Alpha = Angle
        
    def setXoff(self,xoff):
        self.xoff = xoff
        
    def setYoff(self,yoff):
        self.yoff = yoff
        
    def evaluateAtOffset(self,offsetPAngle=0, offsetDist=0, freq=0):
            
        # x-direction is assumed along the meridian in the direction of north celestial pole
        # the offsetPA angle is relative to the meridian
        # the Alpha angle is the rotation of the beam pattern relative to the meridian
        # Therefore the offset relative to the
                
        if (freq > 0):
            self.frequency=freq
            
        x_angle = offsetDist * np.cos(offsetPAngle - self.Alpha)
        y_angle = offsetDist * np.sin(offsetPAngle - self.Alpha)
                    
        x_pb = np.exp(-1.0 * self.expScaling * np.power((x_angle - self.xoff) / self.xwidth, 2.0))
        y_pb = np.exp(-1.0 * self.expScaling * np.power((y_angle - self.yoff) / self.ywidth, 2.0))

        return x_pb * y_pb

def dir_from_ms(ms_name):
    tp = table("%s/FIELD" %(ms_name), readonly=True, ack=False)
    p_phase = tp.getcol('PHASE_DIR')
    tp.close()
    td = table(ms_name, readonly=True, ack=False)
    field = td.getcol("FIELD_ID", 0, 1)[0]
    return SkyCoord(Angle(p_phase[field][0][0], unit=au.rad), Angle(p_phase[field][0][1], unit=au.rad))

def freqs_from_ms(ms_name):
    tf = table("%s/SPECTRAL_WINDOW" %(ms_name), ack=False)
    freqs = tf[0]["CHAN_FREQ"]
    tf.close()
    return freqs

def make_ds9(fname, sources, dMaj, dMin, dPA):
    fout = open(fname, "wt")
    fout.write("# DS9 region file\n")
    fout.write("fk5\n")
    for index in range(len(sources)):
        source = sources[index]
        if dMaj[index] < 1.0 and dMin[index] < 1.0:
            fout.write("point(%f,%f) # point=circle color=red dash=1\n" %(source.ra.deg, source.dec.deg))
        else:
            fout.write("ellipse(%f,%f,%f,%f,%f) # color=red dash=1\n" %(source.ra.deg, source.dec.deg, dMaj[index]/3600.0, dMin[index]/3600.0, 90.0+dPA[index]))
    fout.close()

def flux_nu(S1, alpha, nu1, nu2):
    S0 = S1 / np.power(nu1, alpha)
    return S0 * np.power(nu2, alpha)


def process(ms_name, pb_radii, flux_cutoff, spectral_index = -0.83, catalog_file="./racs-low.fits", freq_cat = 887.5e6):

    model_name = ms_name.replace(".ms", ".model")
    model_reg_name = ms_name.replace(".ms", ".model.reg")
    
    direction = dir_from_ms(ms_name)
    ra_point = direction.ra.deg
    dec_point = direction.dec.deg
    
    galactic_b = direction.galactic.b.deg
    
    dir_str = direction.to_string(style='hmsdms')
    print("Extracting local sky catalogue centred on %s" %(dir_str))
    
    freqs = freqs_from_ms(ms_name)
    freqcent = np.mean(freqs)
    f0 = freqs[0]
    fN = freqs[-1]
    print("Frequency range: %.3f MHz - %.3f MHz (centre = %.3f MHz)" %(f0 / 1.0e6, fN / 1.0e6, freqcent / 1.0e6))
    pb = GaussianPB(frequency = freqcent) #, expscaling=1.09)
    
    radial_cutoff = pb_radii * np.degrees(pb.getFWHM()) # Go out just over 2 times the half-power point.
    print("Radial cutoff = %.3f degrees" %(radial_cutoff))
        
    print("Reading RACS catalogue")
    gsm_cat = Table.read(catalog_file)
    
    n_sources = len(gsm_cat)
    
    print("Generating source coordinates")
    source_directions = SkyCoord(Angle(gsm_cat["RA"], unit=au.deg), Angle(gsm_cat["Dec"], unit=au.deg))
    
    within_field = np.where(direction.separation(source_directions).degree < radial_cutoff)
    field_sources = source_directions[within_field]
    print("Found %d sources in the field" %(len(field_sources)))
    
    source_separations = field_sources.separation(direction).radian
    #print(gsm_cat[within_field])
    sname = gsm_cat["Gaussian_ID"][within_field]
    St = gsm_cat["Total_flux_Gaussian"][within_field]
    dMaj = gsm_cat["DC_Maj"][within_field]
    dMin = gsm_cat["DC_Min"][within_field]
    dPA = gsm_cat["DC_PA"][within_field]
    
    fout = open(model_name, "wt")
    fout.write("Format = Name, Type, Ra, Dec, I, SpectralIndex, LogarithmicSI, ReferenceFrequency='888500000.0', MajorAxis, MinorAxis, Orientation\n")
    total_model_flux = 0.0
    sub_field_sources = []
    sub_dMaj = []
    sub_dMin = []
    sub_dPA = []
    for index in range(len(field_sources)):
        source_direction = field_sources[index]
        dir_str = source_direction.to_string(style='hmsdms',sep=':')
        ra_dec = dir_str.split()
        dec_str = ra_dec[1].replace(':', ".")
        S_cat=float(St[index])/1000.0
        Sref = S_cat / np.power(freq_cat, spectral_index)
        S0 = Sref * np.power(f0, spectral_index)
        S0_pb = S0 * pb.evaluate(source_separations[index], freq=f0)
        if S0_pb < flux_cutoff:
            continue
        SN = Sref * np.power(fN, spectral_index)
        SN_pb = SN * pb.evaluate(source_separations[index], freq=fN)
        alpha = np.log(S0_pb / SN_pb) / np.log(f0 / fN)
        S_ref = flux_nu(S0_pb, alpha, f0, freqcent)
        print("%4d %s s_cat=%.4f S0=%.4f %.4f SN=%.4f %.4f sep=%0.2f deg Sref=%.4f alpha=%.3f" %(index,sname[index],S_cat,S0,S0_pb,SN,SN_pb, np.degrees(source_separations[index]), S_ref, alpha))
    #    alpha=-0.83
        # If source is a gaussian put in type gaussian:
        if dMaj[index] < 1.0 and dMin[index] < 1.0:
            fout.write('s%05d,POINT,%s,%s,%f,[%f,0.0],true,%f,,,\n' %(index, ra_dec[0], dec_str, S_ref, alpha, freqcent))
        else:
            fout.write('s%05d,GAUSSIAN,%s,%s,%f,[%f,0.0],true,%f,%f,%f,%f\n' %(index, ra_dec[0], dec_str, S_ref, alpha, freqcent, dMaj[index], dMin[index], dPA[index]))
        sub_field_sources.append(field_sources[index])
        sub_dMaj.append(dMaj[index])
        sub_dMin.append(dMin[index])
        sub_dPA.append(dPA[index])
        total_model_flux += (S0_pb + SN_pb) / 2.0
    
    fout.close()
    #make_ds9(model_reg_name, sub_field_sources, sub_dMaj, sub_dMin, sub_dPA)
    #print("Total modelled flux = %.3f Jy" %(total_model_flux))

def main(args):
    if args.vis is None:
        raise ValueError("Need to provide an input vis ms")
    else:
        ms_name = args.vis
    pb_radii = args.pb_radii
    flux_cutoff = args.flux_cutoff
    spectral_index = args.spectral_index
    process(ms_name, pb_radii, flux_cutoff, spectral_index)

if __name__ == '__main__':
    a = argparse.ArgumentParser()
    a.add_argument("-vis", type=str, help="Input vis ms")
    a.add_argument("-pb_radii", type=float, help="PB radii (def: 2.0)", default=2.0)
    a.add_argument("-flux_cutoff", type=float, help="Flux cutoff in Jy (def: 0.005)", default = 0.005)
    a.add_argument("-spectral_index", type=float, help="Spectral index (def: -0.83)", default= -0.83)

    args = a.parse_args()
    main(args)
