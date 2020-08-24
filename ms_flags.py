#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ian.heywood@physics.ox.ac.uk


import os
import sys
import glob
import pickle
import numpy
import time
from optparse import OptionParser
from pyrap.tables import table


def get_info(msname):
    tt = table(msname+'/ANTENNA', ack=False)
    ants = tt.getcol('NAME')
    tt.done()
    tt = table(msname+'/SPECTRAL_WINDOW',ack=False)
    spw_chans = numpy.array(tt.getcol('NUM_CHAN'))
    tt.done()
    return ants,spw_chans


def get_flags(msname,ants,spw_chans,scan,field,corr,chan_chunk):
    print('Getting per-antenna flag stats, please wait.')
    flag_stats = []
    tt = table(msname,ack=False)
    for ant in range(0,len(ants)):
        try:
            flag_spectrum = numpy.zeros(numpy.sum(spw_chans/chan_chunk))
        except:
            print('Number of channels divided by chan_chunk must be integer')
            sys.exit()
        t0 = time.time()
        ant_name = ants[ant]
    if field == -1:
            taql = 'ANTENNA1=='+str(ant)+' || ANTENNA2=='+str(ant)
    else:
        taql = 'ANTENNA1=='+str(ant)+' || ANTENNA2=='+str(ant)+' && FIELD_ID=='+str(field)
        if scan != '':
            taql += '&& SCAN_NUMBER=='+str(scan)
        flagtab = tt.query(query=taql,columns='DATA_DESC_ID,FLAG')
        cell_shape = flagtab.getcell('FLAG', 0).shape
        flag_col = numpy.empty((flagtab.nrows(), cell_shape[0], cell_shape[1]), dtype=numpy.bool)
        flagtab.getcolnp('FLAG', flag_col)
        ddid_col = flagtab.getcol('DATA_DESC_ID')
        flagtab.done()
        for dd in range(0,len(spw_chans)):
            interval = spw_chans[dd]/chan_chunk
            i0 = dd*interval
            i1 = ((dd+1)*interval)-1
            mask = ddid_col == dd
            flags = flag_col[mask]
            if len(flags.shape) == 3:
                for ii in range(0,interval):
                    ch0 = ii*chan_chunk
                    ch1 = ((ii+1)*chan_chunk)-1

#                    flag_percent = 100.0*round(flags[:,ch0:ch1,corr].sum() / float(flags[:,ch0:ch1,corr].size),2)

                    vals,counts = numpy.unique(flags[:,ch0:ch1,corr],return_counts=True)
                    if len(vals) == 1 and vals == True:
                        flag_percent = 100.0
                    elif len(vals) == 1 and vals == False:
                        flag_percent = 0.0
                    else:
                        flag_percent = 100.0*round(float(counts[1])/float(numpy.sum(counts)),2)

                    flag_spectrum[i0+ii] = flag_percent
        flag_stats.append((ant_name,flag_spectrum))
        t1 = time.time()
        if ant == 0:
            elapsed = round(t1-t0,2)
            print('First antenna took',elapsed,'seconds,',len(ants)-1,'to go.')
            etc = time.time()+(elapsed*float(len(ants)-1))
            print('Estimated completion at',time.ctime(etc).split()[3]+'.')
    print('Done')
    return flag_stats


def antenna_bar(flag_stats):
    print('')
    print('Flagged percentages per antenna:')
    print('')
    print('                  0%       20%       40%       60%       80%       100%')
    print('                  |         |         |         |         |         |')
    for ii in flag_stats:
        ant = ii[0]
        spectrum = ii[1]
        average_pc = numpy.mean(spectrum)
        length = int(average_pc / 2.0)
        print(' %-9s %-7s %s'% (ant,str(round(average_pc,1))+'%','∎' * length))
    print('')


def freq_bars(ants,spw_chans,flag_stats,chan_chunk):
    print('')
    print('Flagged percentages across the band:')
    print('')
    print('                  0%       20%       40%       60%       80%       100%')
    print('                  |         |         |         |         |         |')
    flag_spec = numpy.zeros(len(flag_stats[0][1]))
    chanranges = []
    for i in range(0,len(flag_spec)):
        flag_chan = []
        for j in range(0,len(ants)):
            flag_chan.append(flag_stats[j][1][i])
        flag_chan = numpy.mean(numpy.array(flag_chan))
        flag_spec[i] = flag_chan
        chanranges.append(str(i*chan_chunk)+'-'+str(((i+1)*chan_chunk)-1))
    for ii in range(0,len(flag_spec)):
        length = int(flag_spec[ii]/2.0)
        print(' %-9s %-7s %s '% (chanranges[ii],str(round(flag_spec[ii],1))+'%','∎' * length))
    print('')


def main():

    parser = OptionParser(usage='%prog [options] msname')
    parser.add_option('--field',dest='field',help='Select field ID (default = all)',default=-1)
    parser.add_option('--corr',dest='corr',help='Select correlation product to use (default = 0)',default=0)
    parser.add_option('--scan',dest='scan',help='Select only a specific scan number (default = all scans)',default='')
    parser.add_option('--noants',dest='doants',help='Do not show per-antenna flags percentages',action='store_false',default=True)
    parser.add_option('--noband',dest='doband',help='Do not show frequency chunk percentages',action='store_false',default=True)
    parser.add_option('--chunk',dest='chan_chunk',help='Number of channels to average per frequency bin (default = 32)',default=32)
    parser.add_option('-o',dest='op_pickle',help='Name of flag stats pickle (default = flag_stats.p, inside MS)',default='')
    parser.add_option('-f',dest='overwrite',help='Force overwrite of existing flag stats pickle',action='store_true',default=False)

    (options,args) = parser.parse_args()
    field = int(options.field)
    corr = int(options.corr)
    scan = options.scan
    doants = options.doants
    doband = options.doband
    chan_chunk = options.chan_chunk
    op_pickle = options.op_pickle
    overwrite = options.overwrite

    if len(args) != 1:
            print('Please specify a Measurement Set')
            sys.exit()
    else:
            msname = args[0].rstrip('/')

    if op_pickle == '':
        op_pickle = msname+'/flag_stats.p'

    ants,spw_chans = get_info(msname)

    if not os.path.isfile(op_pickle) or overwrite:
        flag_stats = get_flags(msname,ants,spw_chans,scan,field,corr,chan_chunk)
        pickle.dump(flag_stats,open(op_pickle,'wb'))
    else:
        print('Reading',op_pickle)
        flag_stats = pickle.load(open(op_pickle,'rb'))

    if doants:
        antenna_bar(flag_stats)

    if doband:
        freq_bars(ants,spw_chans,flag_stats,chan_chunk)


if __name__ == '__main__':

    main()
