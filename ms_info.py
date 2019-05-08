#!/usr/bin/python
# ian.heywood@physics.ox.ac.uk


import sys
import numpy
from astLib import astCoords as ac
from pyrap.tables import table
from optparse import OptionParser


def gi(message):
        print '\033[92m'+message+'\033[0m'


def ri(message):
        print '\033[91m'+message+'\033[0m'


def rad2deg(xx):
	return 180.0*xx/numpy.pi


def main():

        parser = OptionParser(usage='%prog [options] msname')
        parser.add_option('--nofield',dest='dofield',help='Do not list FIELD information',action='store_false',default=True)
        parser.add_option('--noscan',dest='doscan',help='Do not list SCAN information',action='store_false',default=True)
        parser.add_option('--nospw',dest='dospw',help='Do not list SPECTRAL_WINDOW information',action='store_false',default=True)
        parser.add_option('--noant',dest='doant',help='Do not list ANTENNA information',action='store_false',default=True)
        (options,args) = parser.parse_args()
        dospw = options.dospw
        doant = options.doant
        dofield = options.dofield
        doscan = options.doscan

        if len(args) != 1:
                ri('Please specify a Measurement Set')
                sys.exit()
        else:
                myms = args[0].rstrip('/')

        print ''
        gi('Reading: '+myms)
        print ''

        maintab = table(myms,ack=False)
        meanexp = round(numpy.mean(maintab.getcol('EXPOSURE')),2)
        times = maintab.getcol('TIME')
        t0 = times[0]
        t1 = times[-1]
        length = round((t1 - t0),0)

        fldtab = table(myms+'/FIELD',ack=False)
        names = fldtab.getcol('NAME')
        ids = fldtab.getcol('SOURCE_ID')
        dirs = fldtab.getcol('PHASE_DIR')
        fldtab.done()

        if dospw:
                chanwidths = []
                spwtab = table(myms+'/SPECTRAL_WINDOW',ack=False)
                nspw = len(spwtab)
                spwnames = spwtab.getcol('NAME')
                spwfreqs = spwtab.getcol('REF_FREQUENCY')
                for name in spwnames:
                        subtab = spwtab.query(query='NAME=="'+name+'"')
                        chanwidth = subtab.getcol('CHAN_WIDTH')[0][0]/1e6
                        chanwidths.append(chanwidth)
                nchans = spwtab.getcol('NUM_CHAN')
                spwtab.done()

        if doscan:
                scanlist = []
                scans = numpy.unique(maintab.getcol('SCAN_NUMBER'))
                for sc in scans:
                        subtab = maintab.query(query='SCAN_NUMBER=='+str(sc))
                        st0 = subtab.getcol('TIME')[0]
                        st1 = subtab.getcol('TIME')[-1]
                        sfield = numpy.unique(subtab.getcol('FIELD_ID'))[0]
                        st = round((st1-st0),0)
                        nint = int(st/meanexp)
                        scanlist.append((sc,sfield,st,nint))
        	field_integrations = []
        	for fld in ids:
        		tot = 0.0
        		for sc in scanlist:
        			if sc[1] == fld:
        				tot += float(sc[2])
        		field_integrations.append((fld,tot))

        if doant:
                anttab = table(myms+'/ANTENNA',ack=False)
                nant = len(anttab)
                antpos = anttab.getcol('POSITION')
                antnames = anttab.getcol('NAME')
                anttab.done()

                A1 = numpy.unique(maintab.getcol('ANTENNA1'))
                A2 = numpy.unique(maintab.getcol('ANTENNA2'))

                usedants = numpy.unique(numpy.concatenate((A1,A2)))

        maintab.done()

        print '     Track length:             '+str(length)+'s ('+str(round((length/3600.0),2))+' h)'
        print '     Mean integration time:    '+str(meanexp)+' s'
        print ''

        if dofield:
                gi('---- FIELDS:')
                print ''
                gi('     ROW   ID    NAME                RA            DEC')
                for i in range(0,len(names)):
                        ra_rad = dirs[i][0][0]
                        dec_rad = dirs[i][0][1]
                        ra_hms = ac.decimal2hms(rad2deg(ra_rad),delimiter=':')
                        dec_dms = ac.decimal2dms(rad2deg(dec_rad),delimiter=':')
                	print '     %-6s%-6s%-20s%-14s%-14s' % (i,str(ids[i]),names[i],ra_hms,dec_dms)
                print ''

        if doscan:
                gi('---- SCANS:')
                print ''
        	for fld in field_integrations:
        		print '     Total time for field '+str(fld[0])+' is '+str(round(fld[1],0))+' s ('+str(round((fld[1]/3600.0),2))+' h)'
        	print ''
                gi('     SCAN  FIELD_ID      LENGTH[s]     INTEGRATIONS')
                for sc in scanlist:
                        print '     %-6s%-14s%-14s%-14s' % (sc[0],sc[1],sc[2],sc[3])
                print ''

        if dospw:
                gi('---- SPECTRAL WINDOWS:')
                print ''
                gi('     ROW   CHANS         WIDTH[MHz]    REF_FREQ[MHz]')
                for i in range(0,nspw):
                        print '     %-6s%-14s%-14s%-14s' % (i,str(nchans[i]),str(chanwidths[i]),str(spwfreqs[i]/1e6))
                print ''

        if doant:
                gi('---- ANTENNAS:')
                print ''
        	print '     '+str(len(usedants))+' / '+str(nant)+' antennas in the main table'
        	print ''
                gi('     ROW   NAME          POSITION')
                for i in range(0,nant):
                        if i in usedants:
                                print '     %-6s%-14s%-14s' % (i,(antnames[i]),str(antpos[i]))
                        else:
                                ri('     %-6s%-14s%-14s' % (i,(antnames[i]),str(antpos[i])))
                print ''


if __name__ == '__main__':
        main()
