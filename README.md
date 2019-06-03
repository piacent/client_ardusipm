# client_ardusipm
Python scripts for ArduSiPM mqtt client

The main client (whih manages all things related to DAQ
for ArduSiPMs) il pyclient.py.

The script converter.py is a utility script to convert
raw data logfile as blu.TXT and rossa.TXT into a
processed data file (e.g. looking for coincidens and so on).

The scripts pytriggerblu.py, pytriggerrossa.py, sendeblu.py,
and senderrossa.py are intended to be for testing (more info in
the files themselves)

N.B. All the script are tested only on Linux OS  (Ubuntu 18)
for now.
