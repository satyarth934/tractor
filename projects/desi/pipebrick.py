from runbrick import *
import sys
from astrometry.util.ttime import Time, MemMeas
from astrometry.util.plotutils import PlotSequence
import optparse
import logging

import runbrick

if __name__ == '__main__':
    parser = optparse.OptionParser(usage='%prog [options] brick-name-or-number')
    parser.add_option('--threads', type=int, help='Run multi-threaded')
    parser.add_option('--no-ceres', action='store_true', help='Do not use Ceres')
    parser.add_option('--stamp', action='store_true', help='Run a tiny postage-stamp')
    opt,args = parser.parse_args()

    if len(args) != 1:
        parser.print_help()
        sys.exit(-1)


    initargs = dict(W=3600, H=3600, pipe=True)

    brick = args[0]
    try:
        brickid = int(brick, 10)
        initargs.update(brickid=brickid)
    except:
        initargs.update(brickname=brick)

    Time.add_measurement(MemMeas)

    lvl = logging.WARNING
    logging.basicConfig(level=lvl, format='%(message)s', stream=sys.stdout)

    if opt.threads and opt.threads > 1:
        from astrometry.util.multiproc import multiproc

        if True:
            mp = multiproc(opt.threads, init=runbrick_global_init, initargs=())

        else:
            from utils.debugpool import DebugPool, DebugPoolMeas
            dpool = DebugPool(opt.threads, taskqueuesize=2*opt.threads,
                              initializer=runbrick_global_init)
            mp = multiproc(pool=dpool)
            Time.add_measurement(DebugPoolMeas(dpool))
        runbrick.mp = mp
    else:
        runbrick_global_init()

    if opt.no_ceres:
        runbrick.useCeres = False

    if opt.stamp:
        catalogfn = 'tractor-phot-b%06i-stamp.fits' % brick
        pspat = 'pipebrick-plots/brick-%06i-stamp' % brick
        SS = 200
        #initargs.update(W=100, H=100)
        initargs.update(W=SS, H=SS)
    else:
        catalogfn = 'pipebrick-cats/tractor-phot-b%06i.fits' % brick
        pspat = 'pipebrick-plots/brick-%06i' % brick

    P = initargs
    t0 = Time()
    R = stage_tims(**P)
    P.update(R)
    t1 = Time()
    print 'Stage tims:', t1-t0

    R = stage_srcs(**P)
    P.update(R)
    t2 = Time()
    print 'Stage srcs:', t2-t1

    R = stage_fitblobs(**P)
    P.update(R)
    t3 = Time()
    print 'Stage fitblobs:', t3-t2

    R = stage_fitblobs_finish(**P)
    P.update(R)
    t4 = Time()
    print 'Stage fitblobs_finish:', t4-t3

    R = stage_coadds(**P)
    P.update(R)
    t5 = Time()
    print 'Stage coadds:', t5-t4

    P.update(catalogfn=catalogfn)
    stage_writecat(**P)
    t3 = Time()
    print 'Stage writecat:', t3-t2b

    # Plots

    print
    print 'plots:', P.keys()
    print
    
    ps = PlotSequence(pspat)
    P.update(ps=ps, outdir='pipebrick-plots')
    stage_fitplots(**P)
    t4 = Time()
    print 'Stage fitplots:', t4-t3
    print 'Total:', t4 - t0
