#############################################################
# Author: Stefano Piacentini (stefano.piacentini@hotmail.com)
# Date:   04/06/2019
#############################################################


# ========== HERE'S HOW THIS SCRIPT WILL WORK ==========

# This script will convert raw data log files from two ArduSiPM
# into a more suitable shape (e.g. it will convert utc time into
# gps time, sort events by time, find coincidences and so on)

# If you want to run the script without manually insert the needed
# parameters you can edit a file "config.txt" containing
# this lines:

# numberoflogfiles
# nameofthelogfile#1
# nameofthelogfile#2
#     [...]
# nameoftheoutputfile
# timewindow #for coincidences (in us)

# After this try run: $ python3 converter.py < config.txt

# =======================================================


import datetime
import urllib.request
import re

# Be careful in changing this global variables
leap_second=0
# token '$' MUST be the last token in this global vector
tokens = ['g', 'G', 't', 'T', 'v', 's', 'S','K', '$']
hexatokens = ['t', 'T', 'v'] 


# Update leap_second
def update_leap():
	print("\nUpdating leap seconds...")
	link = "ftp://ftp.nist.gov/pub/time/leap-seconds.list"
	f = urllib.request.urlopen(link)
	global leap_second
	for line in f:
		text = line.decode("utf-8")
		if text[0]!='#':
			a, b, *c = text.split('\t')
	leap_second=int(b)
	print("Leap seconds updated: leap_second = "+str(leap_second)+" s")
	

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
	return (total[i])[-3]+0.000001*int((total[i])[2])
def get_det(total, i):
	return (total[i])[-1]	
def time_togps(string):
	global leap_second
	utc = string.replace('g', '')
	y = int(utc[0]+utc[1])+2000
	M = int(utc[2]+utc[3])
	d = int(utc[4]+utc[5])
	h = int(utc[6]+utc[7])
	m = int(utc[8]+utc[9])
	s = int(utc[10]+utc[11])
	utc = datetime.datetime(y, M, d, h, m, s)
	return int(utc.timestamp())-315964819+leap_second

# Functions for tokens handling
def take_value_from(string):
	global tokens
	temp = '['
	cont = 0
	for tok in tokens:
		if tok in string:
			temp = temp + tok + ','
			cont = cont + 1
	temp = temp[:-1] + ']*'
	if cont >= 1:
		temp_vec = re.split(temp[:-1], string)
		return temp_vec[0] 
	elif '\n' in string:
		return string.replace('\n', '')				
def get_tokens_in(string):	
	global tokens
	val_tok = []
	found_tok = []
	if ('@' in string) or (string == '$0\n'):
		return [None,None]
	for tok in tokens:
		if tok in string:
			a,*b = string.split(tok)
			for i in range(0, len(b)):
				val = take_value_from(b[i])
				val_tok.append(val)
				found_tok.append(tok)
	return [val_tok,found_tok]	
def convert_to_decimal(value_tok, which_tok):
	global hexatokens
	temp = []
	for i in range(0, len(value_tok)):
		if which_tok[i] in hexatokens:
			temp.append(str(int(value_tok[i], 16)))
		else:
			temp.append(value_tok[i])
	return temp
def token_occurance(which_tok, tok):
	n = 0
	for i in range(0, len(which_tok)):
		if tok == which_tok[i]:
			n=n+1
	return n
def take_tok_occurance(value_tok, which_tok, tok, n):
	cont = 0
	for i in range(0, len(value_tok)):
		if tok == which_tok[i]:
			cont = cont+1
			if cont==n:
				return value_tok[i]
def take_n_event(which_tok):
	n_occ = []
	for tok in which_tok:
		 n_occ.append(token_occurance(which_tok, tok))
	return max(n_occ)

def parse_detector(filelog):
	nameofDet=get_SN(filelog)
	if nameofDet==None:
		raise Exception('ERROR. SN of detector A not found.')
	
	# Preliminary stuff for parsing
	nO=0
	check=''
	t_diff=''
	ntrueO=calc_oflag(filelog)
	total=[]
	
	global tokens
	
	with open(filelog, 'r') as filelog:
		for line in filelog:
			if '@O' in line:
				nO = nO+1
			elif nO == ntrueO and (('g' in line) or ('G' in line)) and ('@' not in line) and ('$' in line):
				# print(line.replace('\n', '')) # DEBUG #
				value_tok, which_tok = get_tokens_in(line)
				value_tok=convert_to_decimal(value_tok, which_tok)
				# print(value_tok) # DEBUG #
				if value_tok==None:
					continue
				else:
					n_events = take_n_event(which_tok)
					# print("n_events = ", n_events) #DEBUG#
					if n_events!=0:
						for i in range(0, n_events):
							v = []
							for tok in tokens:
								if tok in which_tok:
									n_occ = token_occurance(which_tok, tok)
									# Provisional
									if n_occ != n_events and n_occ!=1:
										raise Exception('ERROR. Something is wrong in tokens structure.')
									if n_occ>1:
										v.append(take_tok_occurance(value_tok, which_tok, tok, i+1))
									else:
										v.append(take_tok_occurance(value_tok, which_tok, tok, 1))
										
								else:
									v.append('-')
							if v[0] != '-':
								v.append(time_togps(v[0]))
								v.append('')
								v.append(nameofDet)
							# print(v) # DEBUG #
							if v[2]!= None and v[2]!='-':
								total.append(v)
							del v
	return total					

def main(filelog, fileout, eps, nDet):
	# Getting the SN of the two detectors
	global tokens
	
	nameofDet = []
	total = []
	for i in range(0,nDet):
		nameofDet.append(get_SN(filelog[i]))
		if nameofDet[i]==None:
			raise Exception('ERROR. SN of detector '+str(i+1)+' not found.')
		total = total + parse_detector(filelog[i])
	
	# Rearrange events by time
	total.sort(key=lambda x: x[-3]+0.000001*int(x[2]))
	
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
					(total[i])[-2]=(total[i])[-2]+',*'
					(total[j+i])[-2]=(total[j+i])[-2]+',*'
					(total[i])[-2]=(total[i])[-2]+',-'+str(int(round(tdiff*1000000,0)))
					(total[j+i])[-2]=(total[j+i])[-2]+','+str(int(round(tdiff*1000000,0)))
	
	# Generating output file
	ffileout=open(fileout, 'w')
	for i in total:
		temp = ''
		temp = temp + 'D,' + i[-1] + ',GPS,'+str(i[-3])
		for j in range(0, len(tokens)):
			temp = temp + ','+tokens[j]+','+i[j]
		temp = temp + i[-2] + '\n'
		ffileout.write(temp)
	ffileout.close()




if __name__ == '__main__':
	print("========================================================\n")
	print("This script will convert the two .TXT files related")
	print("to two ArduSiPM detectors to a .txt file, rearranging")
	print("the events by occurrence time and looking for time ")
	print("coincidences.\n")
	print("========================================================\n")
	nDet = int(input ("Insert the number of file to be converted:"))
	filelog = []
	for i in range(0, nDet):
		filelog.append(input("Insert the path of the .TXT file #"+str(i+1)+":"))
	fileout  = input("Insert the path of the output file:")
	eps = input("Insert time window for coincidences in us:")
	update_leap()
	# Debug print
	print(filelog, fileout, eps, nDet)
	try:
		main(filelog, fileout, int(eps), nDet)
	except Exception as e:
		print(e)
	#input("Premi invio per chiudere questa finestra")
