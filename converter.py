#############################################################
# Author: Stefano Piacentini (stefano.piacentini@hotmail.com)
# Date:   03/06/2019
#############################################################


# ========== HERE'S HOW THIS SCRIPT WILL WORK ==========

# This script will convert raw data log files from two ArduSiPM
# into a more suitable shape (e.g. it will convert utc time into
# gps time, sort events by time, find coincidences and so on)

# If you want to run the script without manually insert the needed
# parameters you can edit a file "config.txt" containing
# this lines:

# nameofthelogfileA
# nameofthelogfileB
# nameoftheoutputfile
# timewindow #for coincidences (in us)

# After this try run: $ python3 converter.py < config.txt

# =======================================================





import datetime
import urllib.request

# Be careful in changing this global variable
leap_seconds=0

# Update leap_seconds
def update_leap():
	print("\nUpdating leap seconds...")
	link = "ftp://ftp.nist.gov/pub/time/leap-seconds.list"
	f = urllib.request.urlopen(link)
	global leap_seconds
	for line in f:
		text = line.decode("utf-8")
		if text[0]!='#':
			a, b, *c = text.split('\t')
	leap_seconds=int(b)
	print("Leap seconds updated: leap_seconds = "+str(leap_seconds)+" s")
	

# Function useful to determine when the detector time is set
def calc_oflag(filelogA):
	n=0;
	with open(filelogA, 'r') as filelog:
		for line in filelog:
			if '@O' in line:
				n=n+1
	if n==0:
		raise Exception('ERROR. Time setting in '+filelogA+' not found.')
		
	return n
		
# Function to get the detector SN 
def get_SN(filelog):
	with open(filelog, 'r') as filelog:
		for line in filelog:
			if '@SN' in line:
				temp, *ts = line.split('@SN')
				return ts[-1].replace('\n', '')
	return None

# Functions useful for coincidences analysis
def get_time(total,i):
	return (total[i])[6]+0.000001*int((total[i])[2])
def get_det(total, i):
	return (total[i])[1]	
def time_togps(string):
	global leap_seconds
	utc = string.replace('g', '')
	y = int(utc[0]+utc[1])+2000
	M = int(utc[2]+utc[3])
	d = int(utc[4]+utc[5])
	h = int(utc[6]+utc[7])
	m = int(utc[8]+utc[9])
	s = int(utc[10]+utc[11])
	utc = datetime.datetime(y, M, d, h, m, s)
	return int(utc.strftime("%s"))-315964819+leap_seconds

def main(filelogA, filelogB, fileout, eps=100):
	# Getting the SN of the two detectors
	nameofA=get_SN(filelogA)
	nameofB=get_SN(filelogB)
	if nameofA==None:
		raise Exception('ERROR. SN of detector A not found.')
	if nameofB==None:
		raise Exception('ERROR. SN of detector B not found.')
	
	# Preliminary stuff for parsing
	nOA=0
	nOB=0
	check=''
	t_diff=''
	ntrueOA=calc_oflag(filelogA)
	ntrueOB=calc_oflag(filelogB)
	total=[]
	
	# Parsing detector A
	with open(filelogA, 'r') as filelogA:
		for lineA in filelogA:
			if '@O' in lineA:
				nOA=nOA+1
			if '$' in lineA and 'g' in lineA and 't' in lineA and nOA==ntrueOA:
				year, *ts = lineA.split('t')
				utc = int(year.replace('g', ''))
				if len(ts) > 0:
					ts[-1], final = ts[-1].split('$')
					for t in ts:
						t, v = t.split('v')
						t = str(int(t, 16))
						v = str(int(v, 16))
						gps=time_togps(year)
						total.append([year, nameofA, t, v, final, check, gps, t_diff])
						
        # Parsing detector B
	with open(filelogB, 'r') as filelogB:
		for lineB in filelogB:
			if '@O' in lineB:
				nOB=nOB+1
			if '$' in lineB and 'g' in lineB and 't' in lineB and nOB==ntrueOB:
				yearb, *tsb = lineB.split('t')
				utcb = int(yearb.replace('g', ''))
				if len(tsb) > 0:
					tsb[-1], finalb = tsb[-1].split('$')
					for tb in tsb:
						tb, vb = tb.split('v')
						tb = str(int(tb, 16))
						vb = str(int(vb, 16))
						gpsb=time_togps(yearb)
						total.append([yearb, nameofB, tb, vb, finalb, check, gpsb, t_diff])
	# Rearrange events by time
	total.sort(key=lambda x: x[6]+0.000001*int(x[2]))

	# Setting the width of the window in which to look for coincidences
	width=20 # Lines
	
	# Check for coincidences
	for i in range(0,len(total)):
		t_i = get_time(total, i)
		det_i = get_det(total, i)
		for j in range(0, width+1):
			if (j+i) < len(total):
				t_ij = get_time(total, j+i)
				tdiff=abs(t_i-t_ij)
				if tdiff<(eps*0.000001) and j!=0 and get_det(total,j+i)!=det_i:
					(total[i])[5]=(total[i])[5]+'*'
					(total[j+i])[5]=(total[j+i])[5]+'*'
					(total[i])[7]=(total[i])[7]+',-'+str(int(round(tdiff*1000000,0)))
					(total[j+i])[7]=(total[j+i])[7]+','+str(int(round(tdiff*1000000,0)))
	
	# Generating output file
	ffileout=open(fileout, 'w')
	for i in total:
		ffileout.write('D,'+i[1]+','+i[0]+',GPS,'+str(i[6])+',t,'+i[2]+',v,'+i[3]+',$,'+ i[4].replace('\n','') + ','+i[5]+i[7]+'\n')
	ffileout.close()




if __name__ == '__main__':
	print("========================================================\n")
	print("This script will convert the two .TXT files related")
	print("to two ArduSiPM detectors to a .txt file, rearranging")
	print("the events by occurrence time and looking for time ")
	print("coincidences.\n")
	print("========================================================\n")
	filelogA = input("Insert the path of the .TXT file - DETECTOR A:")
	filelogB = input("Insert the path of the .TXT file - DETECTOR B:")
	fileout  = input("Insert the path of the output file:")
	eps = input("Insert time window for coincidences in us:")
	update_leap()
	# Debug print
	print(filelogA, filelogB, fileout, eps)
	try:
		main(filelogA, filelogB, fileout, int(eps))
	except Exception as e:
		print(e)
	#input("Premi invio per chiudere questa finestra")
