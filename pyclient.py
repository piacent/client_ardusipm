#############################################################
# Author: Stefano Piacentini (stefano.piacentini@hotmail.com)
# Date:  03/06/2019
#############################################################


# ========== HERE'S HOW THIS SCRIPT WILL WORK ==========

# To start a daq connection you must subscribe to:
#	daqardusipm/pyclient_task
# and publish a massage as follows (pay attention to the
# blank space in the middle of the message):
#       start_daq nameoftheArduSiPM
# A this point any message you want to be processed
# must to be published under the topic:
#	daqardusipm/nameoftheArduSiPM
# (N.B. the DAQ will start only after the time 
#  of the ArduSIPM will be set)
# If you want to stop daq and disconnect the pyclient
# you must to publish the message 'disconnect_client'
# under the topic:
#	daqardusipm/pyclient_task
#

# PAHO-MQTT libraries: (Linux) > pip3 install paho-mqtt
# References: https://pypi.org/project/paho-mqtt/

# =======================================================


import paho.mqtt.client as mqtt
import datetime
import urllib.request
import time
import sys
import os

# Global variables for handling disconnection (be careful in changing
# what regards this variables) or leap seconds
test_disconnection = True
uncorrect_task_out = "The task I'm receiving is not correct."
leap_second  = 0
time_expiration=[-1,-1,-1, False]

# Update leap_seconds
def update_leap():
	print("\nUpdating leap seconds...")
	link = "ftp://ftp.nist.gov/pub/time/leap-seconds.list"
	f = urllib.request.urlopen(link)
	global leap_seconds
	for line in f:
		text = line.decode("utf-8")
		if "expires on" in text:
			thrash, date = text.split(':  ')
			date = date.replace('\n','')
			day, month, year = date.split(' ')
			time_expiration[0]=int(day)
			time_expiration[1]=month[:3]
			time_expiration[2]=int(year)
			time_expiration[3]=True
		if text[0]!='#':
			a, b, *c = text.split('\t')
	leap_second=int(b)
	print("Leap seconds updated: leap_second = "+str(leap_second)+" s")

# ArduSiPM time to GPS time
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
	return int(utc.strftime("%s"))-315964819+leap_second

temp_vec = []

# The callback for when the client receives a response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("daqardusipm/pyclient_task")

# The callback for when a publish message is received from the server.
def on_message(client, userdata, msg):
    # WARNING:: if you use PYTHON 3 you need to decode the payload because
    # in python 3 it's a bytes object (it's an issue of PAHO-MQTT)
    global leap_second
    msg.payload = msg.payload.decode("utf-8")
    text = str(msg.payload)
    if str(msg.topic)=="daqardusipm/pyclient_task":
    	if 'start_daq' in text: 
    		# The following is to be indifferent to the blank spaces between the command and the option
    		ardusipmtostart=(text.replace("start_daq", '')).replace(' ', '')
    		# print(ardusipmtostart) # DEBUG
    		client.subscribe("daqardusipm/"+ardusipmtostart)
    		print("Subscribed to daqardusipm/"+ardusipmtostart)
    		start_flag=False
    		for sublist in temp_vec:
    			if sublist[0]==ardusipmtostart:
    				start_flag=True
    		if start_flag==False:
    			temp_vec.append([ardusipmtostart, False])
    		# print("yes") # DEBUG
    	elif text=="disconnect_client":
    	 	client.loop_stop()
    	 	client.disconnect()
    	 	global test_disconnection
    	 	test_disconnection = False
    	 	print("Exiting from client after disconnection...")
    	 	sys.exit()
    	elif 'end_daq' in text:
    		# The following is to be indifferent to the blank spaces between the command and the option
    		ardusipmtoend=(text.replace("end_daq", '')).replace(' ', '')
 		# If the client receives an end_daq task it must set 
 		# the daq flag of the ArduSiPM to False
    		index_to_end=temp_vec([ardusipmtoend, True])
    		temp_vec[index_to_end]=[ardusipmtoend, False]
    	elif text==uncorrect_task_out:
    		pass
    	else:
    		client.publish("daqardusipm/pyclient_task", uncorrect_task_out)
    else:
    	top=str(msg.topic)
    	ardusipm=top.replace("daqardusipm/", '')
    	# The following is only to avoid taking data
    	# before the detector time setting 
    	tmp_counter=-1
    	for sublist in temp_vec:
    		tmp_counter=tmp_counter+1
    		if sublist[0]==ardusipm:
    			break
    	flag=(temp_vec[tmp_counter])[1]
    	if '@O' in text:
    		ind_temp=temp_vec.index([ardusipm, False])
    		temp_vec[ind_temp]=[ardusipm, True]
    	# DECODING SCRIPT: it adds
    	# a line in a logfile (you can change it to save the line
    	# wherever you want) with the decoded ArduSiPM output
    	# If you follow the instruction in the comment at the
    	# beginning of the page, it will create a logfile for
    	# each ArduSiPM employed in DAQ, automatically.
    	if '$' in text and 'g' in text and flag==True:
    		year, *ts = text.split('t')
    		if len(ts) > 0:
    		      gps=str(time_togps(year))
    		      logfile=open("log_test_"+ardusipm+".txt", "a+")
    		      ts[-1], final = ts[-1].split('$')
    		      for t in ts:
                            t, v = t.split('v')
                            t = str(int(t, 16))
                            v = str(int(v, 16))
                            logfile.write("D,{ardusipm},GPS,{gps},t,{t},v,{v},$,{final}".
                                           format(
                                                    ardusipm=ardusipm,
                                                    gps=gps,
                                                    t=t,
                                                    v=v,
                                                    final=final
                                                ))
    		      logfile.close()
                

    
# Setting the client
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

# TESTING BROKER (if you change broker you must change this)
client.connect("broker.hivemq.com", 1883, 60)


#Start the transmission loop
client.loop_start()

#Check message
client.publish("daqardusipm/pyclient_task", "Client connected to broker.")


# Waiting for disconnection input (one check per second)
# It will also look for changing in
# the global variable 'leap_second' every 3600 s:

while test_disconnection:
	if time_expiration[3]==False:
		update_leap()
		time_counter=0
	else:
		time_exp=datetime.datetime(time_expiration[2], time.strptime(time_expiration[1],'%b').tm_mon, time_expiration[0])
		time_now=datetime.datetime.utcnow()
		deltat=(time_now-time_exp).total_seconds()
		# print(deltat) # DEBUG #
		if(deltat>0):
			update_leap()
	time.sleep(1)
