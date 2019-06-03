#############################################################
# Author: Stefano Piacentini (stefano.piacentini@hotmail.com)
# Date:  03/06/2019
#############################################################


# ========== HERE'S HOW THIS SCRIPT WILL WORK ==========

# This script will start the script "senderrossa.py" when the
# message "trigger" will be published under the topic:
# 	daqardusipm/pyclient_task
# To disconnect, the message "disconnect_sender" should
# be published under the same topic

# PAHO-MQTT libraries: (Linux) > pip3 install paho-mqtt
# References: https://pypi.org/project/paho-mqtt/

# =======================================================

import paho.mqtt.client as mqtt
import time
import sys
import os

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
    	elif text=='trigger':
    		os.system("python3 senderrossa.py")

    
# Setting the client
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

# TESTING BROKER
client.connect("broker.hivemq.com", 1883, 60)


#Start the transmission loop
client.loop_start()

#Check message
client.publish("daqardusipm/pyclient_task", "Trigger client connected to broker.")


# Waiting for disconnection input (one check per second)
while test_disconnection:
	time.sleep(1)
