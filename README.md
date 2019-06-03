# client_ardusipm
## Python scripts for ArduSiPM mqtt client

### Brief description
This github page contains python programs developed by Stefano Piacentini
(PhD. student) with the aim of letting more ArduSiPMs
communicate via wifi with a sort of data center. This is done
using the *mqtt protocol* and, in particular, the *paho-mqtt* python 
library (https://pypi.org/project/paho-mqtt/).

ArduSiPM is a small and cheap particle detector, instead of other cheap 
radiation counter it is not use Geiger effect.  Thanks to new photon 
detector device (the Silicon Photomultiplier) and the advanced technology
of microcontroller system on chip, give the possibility to use the
scintillation detection technique of high energy particles in a small 
and light device powered also by batteries.
Cosmic ray and radiation detection can be a great exploration for teachers,
students and science enthusiasts, and ArduSiPM was created to make it
accessible. The ArduSiPM was designed by a group from
National Institute of Nuclear Physics in Rome (INFN Rome),
led by Dr. Valerio Bocci, an expert in instrumentation for high energy physics.
Their goal was to build a small detection system for beta ray detection and
beam monitoring for the CERN accelerator, but also for testing SiPM technology.
The team was sure about the educational and scientific potential of the project
from the very beginning. A young Italian company (http://www.robot-domestici.it/)
became interested in the project and funded mass-production under INFN license.
ArduSiPM, developed within the INFN, is the first detector in the
scientific literature (DOI: 10.1109 / NSSMIC.2014.7431252) to use a microcontroller
and a limited number of external components to control and acquire a scintillation detector.  

More information in the following  web page:
https://sites.google.com/view/particle-detectors/home

And in the FB group:
https://www.facebook.com/groups/ardusipm/


### Technical details
The main client (which manages all things related to DAQ
for ArduSiPMs) is pyclient.py.

The script converter.py is a utility script to convert
raw data logfile as blu.TXT and rossa.TXT into a
processed data file (e.g. looking for coincidens and so on).

The scripts pytriggerblu.py, pytriggerrossa.py, sendeblu.py,
and senderrossa.py are intended to be for testing (more info in
the files themselves).

**N.B**. All the script are tested only on Linux OS  (Ubuntu 18)
for now (although they seem to work also on other platforms).
Currently, for testing, it will connect to the public mqtt broker
*broker.hivemq.com.*
