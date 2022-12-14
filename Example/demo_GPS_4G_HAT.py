'''
  demo_GPS_4G_HAT.py - This is Finamon GNSS/4G Modem HAT Shield funktionality demo
'''
from datetime import datetime
import time
import pynmea2

import json


import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from Library.BG77X  import BG77X
from Library.MC34X9 import MC34X9
from Library.MC34X9 import MC34X9_RANGE



#----------------------------------------------------------------------------------------
#   JSON stuff
#----------------------------------------------------------------------------------------

gps_json_string = """{
    "imei": 0,
    "latitude": 0,
    "longitude": 0,
    "altitude": 0,
    "utc": 0
}"""


def loc2gps_json (gpsloc):

    mqtt_json = json.loads(gps_json_string)

    mqtt_json['imei'] = int(module.IMEI)

    point = gpsloc['latitude'].find('.')
    gradus = float(gpsloc['latitude'][0:point-2])
    minute = float(gpsloc['latitude'][point-2:-1])/60
    mqtt_json['latitude'] = round(gradus + minute, 6)
    if gpsloc['latitude'][-1] == 'S':
        mqtt_json['latitude'] = - mqtt_json['latitude']

    point = gpsloc['longitude'].find('.')
    gradus = float(gpsloc['longitude'][0:point-2])
    minute = float(gpsloc['longitude'][point-2:-1])/60
    mqtt_json['longitude'] = round(gradus + minute, 6)
    if gpsloc['longitude'][-1] == 'W':
        mqtt_json['longitude'] = - mqtt_json['longitude']

    mqtt_json['altitude'] = gpsloc['altitude']

    dt = datetime(
        2000 + 
        int(gpsloc['date'][4:]),    # year
        int(gpsloc['date'][2:4]),
        int(gpsloc['date'][0:2]),
        int(gpsloc['time'][0:2]),    # hour
        int(gpsloc['time'][2:4]),
        int(gpsloc['time'][4:6]),
        )
    mqtt_json['utc'] = dt.timestamp()
    return mqtt_json

def writeNMAlog (file):

    head = "+QGPSGNMEA: "

#     module.sendATcmd('AT+QGPSGNMEA="GSV"')
#     start = module.response.find(head)
#     while start != -1:
#         start += len(head)
#         end = module.response.find(head, start)
#         if end == -1:
#             file.write(module.response[start:module.response.find("OK", start) - 2])
#             break;
#         file.write(module.response[start:end])
#         start = end
        
    module.sendATcmd('AT+QGPSGNMEA="RMC"')
    start = module.response.find(head)
    end = module.response.find("*", start) + 3
    nmea_sent = module.response[start + len(head) : end]
    file.write(nmea_sent + '\r\n')
    file.flush()
    
    try:
        msg = pynmea2.parse(nmea_sent)
    except Exception: 
        return False  #return on parser exception 
    
    if msg.lat:
        mqtt_json = json.loads(gps_json_string)
        mqtt_json['imei'] = int(module.IMEI)
        mqtt_json['latitude'] = round(msg.latitude, 6)
        mqtt_json['longitude'] = round(msg.longitude, 6)
        mqtt_json['altitude'] = 0
        mqtt_json['utc'] = msg.datetime.timestamp()
    else:
       mqtt_json = False

    return mqtt_json



#----------------------------------------------------------------------------------------
#   network access and MQTT service data
#----------------------------------------------------------------------------------------
sim_apn = "wsim"

mqtt_broker = '23.88.108.59'
mqtt_port = 1883
mqtt_client_id = 'TBD'
mqtt_username = 'api'
mqtt_password = 'flake-iraq-contra'
mqtt_topic = "gps/coordinates"


#----------------------------------------------------------------------------------------
#   init GPS/communication module BG77x and data structures
#----------------------------------------------------------------------------------------
accel = MC34X9()

SAMPLE_RATE = 0x10
AM_DEBOUNCE = 5
AM_THRESHOLD = 150

accel.setStandbyMode()                      #Put accelerometer in standby mode
accel.setGPIOControl(0b00001100)            #Set GPIO control. Set bit 2 to 1 for INT active high, set bit 3 to 1 for INT push-pull
accel.setSampleRate(SAMPLE_RATE)            #Set the sample rate

accel.setInterrupt(0b00000100)              #Set the interrupt enable register, bit 0 enables tilt, bit 1 enables flip, bit 3 enables shake. Set bit 6 to 1 for autoclear
accel.setAnymotionThreshold(AM_THRESHOLD)   #Set tilt threshold
accel.setAnymotionDebounce(AM_DEBOUNCE)     #Set tilt debounce
accel.setMotionControl(0b00000100)          #Enable motion control features. Bit 0 enables tilt/flip, bit 2 enables anymotion (req for shake), bit 3 enables shake, bit 5 inverts z-axis

accel.setRange(MC34X9_RANGE.RANGE_2G.value) #Set accelerometer range
accel.clearInterrupts()                     #Clear the interrupt register
accel.resetMotionControl()                  #Reset the motion control
accel.setWakeMode()                         #Wake up accelerometer

accel.readAccel()
accel.printAccel()

module = BG77X()

module.sendATcmd("AT")
module.getHardwareInfo()
module.getFirmwareInfo()
module.getIMEI()

#module.acquireGnssSettings()
file = open("../nmea_60sec.log", "a")
file.write("\nIMEI: %s\n" % module.IMEI)

while True:
#----------------------------------------------------------------------------------------
#   detect any motion
#----------------------------------------------------------------------------------------

    print ("\nmove shield to start")
    while accel.getStatus() == 0xA0:
        time.sleep(1.)
    accel.readAccel()
    print("motion detected: ", end='')
    accel.printAccel()
   
    if not module.isOn():
        module.open()
    module.gnssOn()

#----------------------------------------------------------------------------------------
#   get current geoposition
#----------------------------------------------------------------------------------------

    start_time = time.time()
    mqtt_json = writeNMAlog(file)
    while(not mqtt_json):
        time.sleep(10.)
        mqtt_json = writeNMAlog(file)
    print ("\nposition search time %s seconds\n" % int(time.time() - start_time))
    
    for sec in range (30):      
        mqtt_json = writeNMAlog(file)
        time.sleep(.99)

    module.gnssOff()
    time.sleep(2.)

#----------------------------------------------------------------------------------------
#   send current geoposition to MQTT server
#----------------------------------------------------------------------------------------

    if (mqtt_json):
        print("\nhttps://maps.google.com/?q=%s,%s\n" % (mqtt_json['latitude'], mqtt_json['longitude']))
        mqtt_msg = json.dumps(mqtt_json)
    else:
        continue

    module.getHardwareInfo()
    module.getFirmwareInfo()
    module.getIMEI()

    contextID = "1"
    if module.initNetwork(contextID, sim_apn):
        module.activatePdpContext(contextID, 5)

        mgtt_client_idx = "0"
        mqtt_client_id_string = module.IMEI
        module.openMqttConnection(mgtt_client_idx, mqtt_broker, mqtt_port)
        module.connectMqttClient(mqtt_client_id_string, mqtt_username, mqtt_password)

        module.publishMqttMessage(mqtt_topic, mqtt_msg)

        module.sendATcmd("AT+QMTDISC=0", "+QMTDISC:", 10)
        module.closeConnection()
        module.deactivatePdpContext(contextID, 5)

    module.close()
    time.sleep(2.)

#51.229047, 6.714671 work
