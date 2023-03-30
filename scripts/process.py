import os

# Remove the averaged/converted ms from previous run
os.system("rm -fr SB42431_tscrunch_v6_aver.ms SB42431_tscrunch_v6_aver_1pol.ms SB42431_tscrunch_v6_aver_4polA.ms SB42431_tscrunch_v6_aver_4polB.ms")
# Average the ms to allow calibration to complete within the time-scale of the Universe
split(vis='SB42431_tscrunch_v6.ms',outputvis='SB42431_tscrunch_v6_aver.ms',timebin='10s', datacolumn='data')
# Create a single-pol version of the data (combine XX and YY)
split(vis='SB42431_tscrunch_v6_aver.ms',outputvis='SB42431_tscrunch_v6_aver_1pol.ms',correlation='XX', datacolumn='data')

# Convert the 2 pol MS into a 4 pol MS
os.system("./convert.py SB42431_tscrunch_v6_aver.ms SB42431_tscrunch_v6_aver_4polA.ms")
# Convert the 1 pol MS into a 4 pol MS
os.system("./convert.py SB42431_tscrunch_v6_aver_1pol.ms SB42431_tscrunch_v6_aver_4polB.ms")

# Extract a model for wherever this MS is pointing
os.system("extract_model_for_ms.py SB42431_tscrunch_v6_aver.ms 2.0 0.005")

# Calibrate 2-pol data against the model
os.system("calibrate -minuv 200.0 -m SB42431_tscrunch_v6_aver.model SB42431_tscrunch_v6_aver_4polA.ms SB42431_tscrunch_v6_aver_4polA.bin")
# Calibrate 1-pol data against the model
os.system("calibrate -minuv 200.0 -m SB42431_tscrunch_v6_aver.model SB42431_tscrunch_v6_aver_4polB.ms SB42431_tscrunch_v6_aver_4polB.bin")

# Apply the solution to the 2 pol and 4 pol ms (this creates the CORRECTED_DATA column)
os.system("./applysolutions SB42431_tscrunch_v6_aver.ms SB42431_tscrunch_v6_aver_4pol.bin")
os.system("./applysolutions SB42431_tscrunch_v6_aver_4polA.ms SB42431_tscrunch_v6_aver_4polA.bin")
os.system("./applysolutions SB42431_tscrunch_v6_aver_4polB.ms SB42431_tscrunch_v6_aver_4polB.bin")
# Flag any crap that might be in the data
os.system("./flag.py SB42431_tscrunch_v6_aver.ms")
os.system("./flag.py SB42431_tscrunch_v6_aver_4polA.ms")
os.system("./flag.py SB42431_tscrunch_v6_aver_4polB.ms")

# Clean up from previous imaging run
os.system("rm -fr im2pol* test_im2pol*")
tclean(vis='SB42431_tscrunch_v6_aver.ms',datacolumn='corrected',imagename='im2pol',imsize=[2000],cell=['2.0arcsec'],pblimit=-0.1,weighting='briggs',robust=0.0, niter=100)
# Convert to fits and remove all intermediate files
ia.open("im2pol.image")
ia.tofits("test_im2pol.fits")
ia.close()
os.system("rm -fr im2pol*")


# Clean up from previous imaging run
os.system("rm -fr im4polA* test_im4polA*")
tclean(vis='SB42431_tscrunch_v6_aver_4polA.ms',datacolumn='corrected',imagename='im4polA',imsize=[2000],cell=['2.0arcsec'],pblimit=-0.1,weighting='briggs',robust=0.0, niter=100)
# Convert to fits and remove all intermediate files
ia.open("im4polA.image")
ia.tofits("test_im4polA.fits")
ia.close()
os.system("rm -fr im4polA*")

# Clean up from previous imaging run
os.system("rm -fr im4polB* test_im4polB*")
tclean(vis='SB42431_tscrunch_v6_aver_4polB.ms',datacolumn='corrected',imagename='im4polB',imsize=[2000],cell=['2.0arcsec'],pblimit=-0.1,weighting='briggs',robust=0.0, niter=100)
# Convert to fits and remove all intermediate files
ia.open("im4polB.image")
ia.tofits("test_im4polB.fits")
ia.close()
os.system("rm -fr im4polB*")
