#############################################################
# Author: Stefano Piacentini (stefano.piacentini@hotmail.com)
# Date:  03/06/2019
#############################################################


# ========== HERE'S HOW THIS SCRIPT WILL WORK ==========

# This script will start a daq session for the pyclient.py
# script. It will send the content of "rossa.TXT" file.

# To disconnect, the message "disconnect_sender" should
# be published under the same topic

# PAHO-MQTT libraries: (Linux) > pip3 install paho-mqtt
# References: https://pypi.org/project/paho-mqtt/

# =======================================================

import paho.mqtt.client as mqtt
import time
import sys
import os

def file_len(fname):
    i=0
    with open(fname, 'r') as f:
        for line in f:
        	i=i+1
    return i


# global variable for handling disconnection (be careful in changing
# what regards this variable)
test_disconnection = True

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
    msg.payload = msg.payload.decode("utf-8")
    text = str(msg.payload)
    if str(msg.topic)=="daqardusipm/pyclient_task":
    	if text=="disconnect_sender":
    	 	client.loop_stop()
    	 	client.disconnect()
    	 	global test_disconnection
    	 	test_disconnection = False
    	 	# print(str(test))
    	 	print("Exiting from client after disconnection...")
    	 	sys.exit()
    		              

    
# Setting the client
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

# TESTING BROKER
client.connect("broker.hivemq.com", 1883, 60)

time.sleep(1)

#Start the transmission loop
client.loop_start()

time.sleep(1)
#Check message
client.publish("daqardusipm/pyclient_task", "start_daq ARDU_ROSSA")
time.sleep(0.5)

file_path = "rossa.TXT"
l=file_len(file_path)

i_cont=0
n_prev=999
with open(file_path, 'r') as logfile:
	for line in logfile:
		client.publish("daqardusipm/ARDU_ROSSA", line)
		p_cont=i_cont*100/l
		n_cont=int((p_cont)/10)
		if n_prev!=n_cont:
			print(str(n_cont*10)+' % sent.')
		if i_cont==l-1:
			time.sleep(0.5)
			client.publish("daqardusipm/pyclient_task", "end_daq ARDU_ROSSA")
			print("DAQ ended.")
		time.sleep(0.01)
		i_cont=i_cont+1
		n_prev=n_cont


# Waiting for disconnection input (one check per second)
while test_disconnection:
	time.sleep(1)
