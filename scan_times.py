#!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk


from astropy.time import Time
from pyrap.tables import table
import numpy
import sys

def main():

	myms = sys.argv[1]

	tt = table(myms,ack=False)
	scan_numbers = list(set(tt.getcol('SCAN_NUMBER')))
	n_scans = len(scan_numbers)
	exposure = round(numpy.mean(tt.getcol('EXPOSURE')),4)
	field_tab = table(myms+'/FIELD',ack=False)
	field_names = field_tab.getcol('NAME')
	n_fields = len(field_names)
	field_tab.done()

	print(myms+' | '+str(n_fields)+' fields | '+str(n_scans)+' scans | t_int = '+str(exposure)+' s')
	header = 'Scan  Field        ID    t[iso]                    t[s]                 t0[s]                t1[s]                Duration[m]  N_int'
	print('-'*len(header))
	print(header)
	print('-'*len(header))
	for scan in scan_numbers:
		subtab = tt.query(query='SCAN_NUMBER=='+str(scan))
		times = subtab.getcol('TIME')
		field_id = list(set(subtab.getcol("FIELD_ID")))[0]
		field_name = field_names[field_id]
		subtab.done()

		t0 = times[0]
		t1 = times[-1]
		dt = (t1-t0)
		duration = round((dt/60.0),2)
		n_int = int(dt / exposure)
		tc = t0+(dt/2.0)
		t_iso = Time(tc/86400.0,format='mjd').iso

		print('%-5i %-12s %-5s %-25s %-20f %-20f %-20f %-12s %-5i' % (scan,field_name,field_id,t_iso,tc,t0,t1,duration,n_int))

	print('-'*len(header))
	tt.done()


if __name__ == "__main__":

    main()