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
# timewindow #for coincidences (in ns)

# After this try run: $ python3 converter.py < config.txt

# N. B.
# If SN is not in the input files, the script will ask you for it.
# So if you are using the "config.txt" you must add lines for each
# file in which the SN is missing (in order).

# =======================================================


import datetime
import urllib.request
import re
import sys

# Be careful in changing this global variables
leap_second=0
# If you have to add new tokens, add them before '$' 
# and after the last token before '$' (the order MUST be this)
tokens = ['g', 'G', 't', 'T', 'v', 's', 'S','K', '$']
hexatokens = ['t', 'T', 'v'] 


# Update leap_second
def update_leap():
	global leap_second
	print("\nUpdating leap seconds...")
	link = "ftp://ftp.nist.gov/pub/time/leap-seconds.list"
	try:
		f = urllib.request.urlopen(link, timeout=10)
		for line in f:
			text = line.decode("utf-8")
			if text[0]!='#':
				a, b, *c = text.split('\t')
		leap_second=int(b)
		print("Leap seconds updated: leap_second = "+str(leap_second)+" s")
	except:
		print("WARNING: Unable to update leap seconds, which are now set to 0.")
		leap_second = 0
	
	

# Function useful to determine when the detector time is set
def calc_oflag(filelogA):
	n=0;
	with open(filelogA, 'r') as filelog:
		for line in filelog:
			if '@O' in line:
				n=n+1
	if n==0:
		print('\nWarning. Time setting in '+filelogA+' not found. All data will be taken into account.')
		sys.stdout.flush()
		
	return n
		
# Function to get the detector SN 
def get_SN(filelog):
	SN = None
	with open(filelog, 'r') as filelog:
		for line in filelog:
			if '@SN' in line:
				temp, *ts = line.split('@SN')
				SN = ts[-1].replace('\n', '')
	return SN

# Functions useful for coincidences analysis
def get_time(total,i):
	return (total[i])[-3] % 86400 + 0.000001*float((total[i])[2])
def get_time_diff(total, i, j): # Assuming time window for coincidences always
				# smaller than 1s
	t_i = get_time(total, i)
	t_j = get_time(total, j)
	intt_i = (total[i])[-3]
	intt_j = (total[j])[-3]
	tdiff    = abs(t_i - t_j)
	inttdiff = abs(intt_i - intt_j)
	if inttdiff==1 and int(tdiff)==86399:
		ret = 86400 + min(t_i, t_j) - max(t_i, t_j)
	else:
		ret = tdiff
	return ret;
def get_det(total, i):
	return (total[i])[-1]	
def time_togps(utc):
	global leap_second
	y = int(utc[0]+utc[1])+2000
	M = int(utc[2]+utc[3])
	d = int(utc[4]+utc[5])
	h = int(utc[6]+utc[7])
	m = int(utc[8]+utc[9])
	s = int(utc[10]+utc[11])
	utc = datetime.datetime(y, M, d, h, m, s)
	return int(utc.timestamp())-315964819+leap_second

# Functions for tokens handling
def take_value_from(string):   # Function useful for the function "get_token_in"
			       # (print temp if you want to understand better it's behaviour,
			       # however it uses regular expressions, you
			       # can find documentation on https://docs.python.org/3/library/re.html)
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
	else:
		return string		
			
def get_tokens_in(string):	# Function to convert the string to two list:
				# + a list with all values
				# + a list with all corrisponding tokens
	global tokens
	val_tok = []
	found_tok = []
	if ('@' in string) or (string == '$0\n'):
		return [None,None]
	for tok in tokens:
		if tok in string:
			#print(" tok = ", tok, end ='       ')
			a,*b = string.split(tok)
			#print(" b  =   ", b)
			for i in range(0, len(b)):
				val = take_value_from(b[i])
				val_tok.append(val)
				found_tok.append(tok)
	#print(val_tok, "    ", found_tok)
	return [val_tok,found_tok]	
	
def convert_to_decimal(value_tok, which_tok):       # Function returning converted decimal value
						    # for hexa tokens
	global hexatokens
	temp = []
	for i in range(0, len(value_tok)):
		if which_tok[i] in hexatokens:
			#print(value_tok[i], "  ", which_tok[i])
			temp.append(str(int(value_tok[i], 16)))
		else:
			temp.append(value_tok[i])
	return temp
	
def token_occurrence(which_tok, tok):		# Function to get the occurrence of the token tok
						# in a given decomposed line which_tok (that
						# is to say how many times tok is in whick_tok)
	n = 0
	for i in range(0, len(which_tok)):
		if tok == which_tok[i]:
			n=n+1
	return n
	
def take_tok_occurrence(value_tok, which_tok, tok, n):      # Function to return the VALUE related to
							    # the n-th occurrence of the token tok
	cont = 0
	for i in range(0, len(value_tok)):
		if tok == which_tok[i]:
			cont = cont+1
			if cont==n:
				return value_tok[i]				
				
def take_n_event(which_tok):			# Number of events in a line is equivalent
						# to the most frequent token (e.g. if I have
						# 2 't' or 2 'T' i have 2 events; this is
						# because '$' is not always the number of events
						# and because '$' is not present in cosmic formatting
	n_occ = []
	for tok in which_tok:
		 n_occ.append(token_occurrence(which_tok, tok))
	return max(n_occ)
	
def get_gsvalue(string):			# Function to get time values of a string
	if (('s' in string) or ('S' in string)) and (('g' in string) or ('G' in string)):
		g=None
		s=None
		value_tok, which_tok = get_tokens_in(string)
		value_tok=convert_to_decimal(value_tok, which_tok)
		for i in range(0, len(value_tok)):
			if 'g' == which_tok[i]:
				g=value_tok[i]
			# G and g cannot be on the same line
			if 'G' == which_tok[i]:
				g=value_tok[i]
			if 's' == which_tok[i]:
				s=value_tok[i]
			# S and s cannot be on the same line
			if 'S' == which_tok[i]:
				s=value_tok[i]
		return [g,s]
	else:
		raise Exception("\nERROR. Something went wrong in get_sgline.") 

# Function for file parsing
def parse_detector(filelog):
	nameofDet=get_SN(filelog)
	if nameofDet==None:
		sys.stdout.flush()
		nameofDet = input("SN not found in file " + filelog +". Please insert the corrisponding SN: ")
	
	# Preliminary stuff for parsing
	nO=0
	check=''
	t_diff=''
	ntrueO=calc_oflag(filelog)
	total=[]
	first_g = False
	gpstime=-1
	s_line=-1
	
	global tokens
	
	with open(filelog, 'r') as filelog:
		for line in filelog:
		
			# This is only for cosmic format stuff
			if nO == ntrueO and (('S' in line) or ('s' in line)) and gpstime!=-1 and ('@' not in line):
				
				value_tok, which_tok = get_tokens_in(line)
				value_tok=convert_to_decimal(value_tok, which_tok)
				for i in range(0, len(value_tok)):
					if 's' == which_tok[i]:
						s_new = value_tok[i]
					# S and s cannot be on the same line
					if 'S' == which_tok[i]:
						s_new = value_tok[i]
				d = int(s_new)-int(s_line)
				if d<0:
					gpstime = gpstime + (60+d)
				else: 
					gpstime = gpstime + d
					
				
				gpstime = gpstime + (int(s_new)-int(s_line))
				
				s_line=s_new
				
			if '@O' in line:
				nO = nO+1	
			
			# This is for regular formatting
			elif nO == ntrueO and (('g' in line) or ('G' in line)) and ('@' not in line) and ('$' in line):
				
				value_tok, which_tok = get_tokens_in(line)
				value_tok=convert_to_decimal(value_tok, which_tok)
				
				if value_tok==None:
					continue
				else:
					n_events = take_n_event(which_tok)
					
					if n_events!=0:
						for i in range(0, n_events):
							v = []
							for tok in tokens:
								if tok in which_tok:
									n_occ = token_occurrence(which_tok, tok)
									# Provisional
									if n_occ != n_events and n_occ!=1:
										raise Exception('\nERROR. Something is wrong in tokens structure.')
									if n_occ>1:
										v.append(take_tok_occurrence(value_tok, which_tok, tok, i+1))
									else:
										v.append(take_tok_occurrence(value_tok, which_tok, tok, 1))
										
								else:
									v.append('-')
							# Here is when the order in tokens is important
							# Case g 
							if v[0] != '-' and v[1] == '-':
								v.append(time_togps(v[0]))
								v.append('')
								v.append(nameofDet)
							# Case G
							elif v[1] != '-' and v[0] == '-':
								v.append(time_togps(v[1]))
								v.append('')
								v.append(nameofDet)
							# If the line has a 't' (regular format)
							if v[2]!= None and v[2]!='-':
								total.append(v)
							# If the line does not have a 't' but has a 'T', a
							# corrispondent 't' is produced with a ns precision
							elif (v[2]== None or v[2]=='-') and (v[3] != None and v[3]!= '-') :
								v[2] = str(int(int(v[3])*1000000000./int(v[7]))/1000.)
								total.append(v)
							
							del v
							
			# This is for cosmic formatting	
			elif nO == ntrueO and 'K' in line and 'T' in line and (('S' in line) or ('s' in line)):
				if 'g' in line and first_g == False:
					first_g = True
					g_line, s_line = get_gsvalue(line)
					gpstime = time_togps(g_line)
					
				if first_g == True:
					value_tok, which_tok = get_tokens_in(line)
					value_tok=convert_to_decimal(value_tok, which_tok)
					
					if value_tok==None:
						continue
					n_events = take_n_event(which_tok)
					if n_events!=0:
						for i in range(0, n_events):
							v = []
							for tok in tokens:
								if tok in which_tok:
									n_occ = token_occurrence(which_tok, tok)
									# Provisional
									if n_occ != n_events and n_occ!=1:
										raise Exception('\nERROR. Something is wrong in tokens structure.')
									if n_occ>1:
										v.append(take_tok_occurrence(value_tok, which_tok, tok, i+1))
									else:
										v.append(take_tok_occurrence(value_tok, which_tok, tok, 1))
									
								else:
									v.append('-')
							# Here is when the order in tokens is important
							v[1] = str(gpstime)
							v.append(gpstime)
							v.append('')
							v.append(nameofDet)
							
							v[2] = str(int(float(v[3])/float(v[7])*1000000.))
							
							if v[2]!= None and v[2]!='-':
								total.append(v)
							del v
							
	return total					

def main(filelog, fileout, eps, nDet):
	
	global tokens
	
	total = []
	
	# Parsing files
	for i in range(0,nDet):
		total = total + parse_detector(filelog[i])
	
	# Rearrange events by time
	total.sort(key=lambda x: x[-3] + 0.000001*float(x[2]))
	
	# Setting the width of the window in which to look for coincidences
	width=20 # Lines
	
	# Check for coincidences
	for i in range(0,len(total)):
		det_i = get_det(total, i)
		for j in range(0, width+1):
			if (j+i) < len(total):
				tdiff= get_time_diff(total, i, j+i)
				if tdiff<(eps*1.e-9) and j!=0 and get_det(total,j+i)!=det_i:
					(total[i])[-2]=(total[i])[-2]+',*'
					(total[j+i])[-2]=(total[j+i])[-2]+',*'
					(total[i])[-2]=(total[i])[-2]+',-'+str(int(round(tdiff*1.e9)))
					(total[j+i])[-2]=(total[j+i])[-2]+','+str(int(round(tdiff*1.e9)))
	
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
	eps = input("Insert time window for coincidences in ns:")
	update_leap()
	# Debug print
	print(filelog, fileout, eps, nDet)
	try:
		main(filelog, fileout, int(eps), nDet)
	except Exception as e:
		print(e)
	#input("Premi invio per chiudere questa finestra")
