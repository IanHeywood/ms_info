#!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk


from astropy.time import Time
from pyrap.tables import table
import numpy
import sys


def main():

	if len(sys.argv) == 1:
		print('Please specify a Measurement Set')
		sys.exit()
	elif len(sys.argv) > 1:
		myms = sys.argv[1]

	if len(sys.argv) > 2:
		myscan = sys.argv[2]
	else:
		myscan = ''

	tt = table(myms,ack=False)
	all_times = list(numpy.unique(tt.getcol('TIME')))
	track_length = round(((all_times[-1] - all_times[0]) / 3600.0),3)
	scan_numbers = list(set(tt.getcol('SCAN_NUMBER')))
	n_scans = len(scan_numbers)
	exposure = round(numpy.mean(tt.getcol('EXPOSURE')),4)
	field_tab = table(myms+'/FIELD',ack=False)
	field_names = field_tab.getcol('NAME')
	n_fields = len(field_names)
	field_tab.done()

	print(myms+' | '+str(n_fields)+' fields | '+str(n_scans)+' scans | track = '+str(track_length)+' h | t_int = '+str(exposure)+' s')

	if myscan == '':
		header = 'Scan  Field        ID    t[iso]                    t[s]                 t0[s]                t1[s]                int0    int1    Duration[m]  N_int'
		print('-'*len(header))
		print(header)
		print('-'*len(header))
		for scan in scan_numbers:
			subtab = tt.query(query='SCAN_NUMBER=='+str(scan))
			times = subtab.getcol('TIME')
			field_id = list(set(subtab.getcol("FIELD_ID")))[0]
			field_name = field_names[field_id]
			subtab.done()

			t0 = times[0] # start time for this scan 
			t1 = times[-1] # end time for this scan
			int0 = all_times.index(t0) # start interval number in the full MS
			int1 = all_times.index(t1) # end interval number in the full MS
			dt = (t1-t0) # duration of this scan
			duration = round((dt/60.0),2) # duration in minutes
			n_int = int(dt / exposure) # number of integration times in this scan
			tc = t0+(dt/2.0) # central time of this scan 
			t_iso = Time(tc/86400.0,format='mjd').iso # central time of this scan in ISO format

			print('%-5i %-12s %-5s %-25s %-20f %-20f %-20f %-7s %-7s %-12s %-5i' % 
				(scan,field_name,field_id,t_iso,tc,t0,t1,int0,int1,duration,n_int))

		print('-'*len(header))

	else:

		subtab = tt.query(query='SCAN_NUMBER=='+str(myscan))
		times = numpy.unique(subtab.getcol('TIME'))
		subtab.done()

		print('Per-integration time details for scan '+myscan)
		header = 't[iso]                    t[s]                 int'
		print('-'*len(header))
		print(header)
		print('-'*len(header))
		for t_i in times:
			t_iso = Time(t_i/86400.0,format='mjd').iso
			int_i = all_times.index(t_i)
			print('%-25s %-20f %-7s' %
				(t_iso,t_i,int_i))
		print('-'*len(header))

	tt.done()


if __name__ == "__main__":

    main()
