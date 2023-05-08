from casatasks import split
import argparse

def process(vis, outvis, timebin, freqbin, datacolumn = 'data'):
    # add function to determine the frequency bin width
    cracovis = SimpleMeasurementSet(vis)
    width = int(freqbin*1e6 // cracovis.foff)
    split(vis=vis, outputvis=outvis, timebin=timebin, width=width, datacolumn=datacolumn)

def main(args):
    if args.vis is None:
        raise ValueError("Need an input vis to process")
    else:
        vis = args.vis
    
    if args.outvis is None:
        outvis = vis.strip("ms") + "aver.ms"
    else:
        outvis = args.outvis

    timebin = str(args.timebin) + 's'

    process(vis, outvis, timebin)

if __name__== '__main__':
    a = argparse.ArgumentParser()
    a.add_argument("-vis", type=str, help="Input visibility ms")
    a.add_argument("-outvis", type=str, help="Output visibility ms", default=None)
    a.add_argument("-timebin", type=float, help="Sampling time (in seconds) of the output vis ms (def:10)", default=10)

    args = a.parse_args()
    main(args)


