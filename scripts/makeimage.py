import os
import sys
import datetime

target = sys.argv[3]
print(target)

default(tclean)
# Make a dirty image at FRB time -10s
tclean(vis=target,datacolumn='corrected',imagename=target+'.dirty',imsize=[2048],cell=['2arcsec'],pblimit=-0.1,weighting='briggs',robust=0.0,gridder='widefield',wprojplanes=-1,niter=0)
ia.open(target+".dirty.image")
ia.tofits(target+".dirty.fits")
ia.close()

# Make a dirty image at FRB time 0s
#tclean(vis=target,datacolumn='corrected',imagename='frb_n1e4_15min',imsize=[2048],cell=['2arcsec'],pblimit=-0.1,weighting='briggs',robust=0.0,gridder='widefield',wprojplanes=-1,niter=10000,phasecenter=phasecent)
#ia.open("frb_n1e4_15min.image")
#ia.tofits("frb_n1e4_15min.fits")
#ia.close()



