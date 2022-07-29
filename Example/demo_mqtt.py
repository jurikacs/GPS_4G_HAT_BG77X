'''
  demo_echo.py - This is basic Finamon GNSS/4G Modem HAT Shield mqqt example.
'''
import json
import time

import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from Library.BG77X import BG77X

gps_json_string = """{
    "imei": 0,
    "latitude": 0,
    "longitude": 0,
    "altitude": 0,
    "utc": 0
}"""

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

module = BG77X()
module.debug_print("MQTT client demo")

module.sendATcmd("AT")
module.getHardwareInfo()
module.getFirmwareInfo()
module.getIMEI()

mqtt_json = json.loads(gps_json_string)
mqtt_json['imei'] = int(module.IMEI)
mqtt_json['latitude'] = 3.141596
mqtt_json['longitude'] = 2.718282
mqtt_json['altitude'] = 0
mqtt_json['utc'] = int(time.time())
mqtt_msg = json.dumps(mqtt_json)

contextID = "1"
if module.initNetwork(contextID, sim_apn):
    module.activatePdpContext(contextID, 5)

    mgtt_client_idx = "0"
    mqtt_client_id_string = module.IMEI
    module.openMqttConnection(mgtt_client_idx, mqtt_broker, mqtt_port)
    module.connectMqttClient(mqtt_client_id_string, mqtt_username, mqtt_password)

    module.publishMqttMessage(mqtt_topic, mqtt_msg)

    #module.subscribeToMqttTopic(mqtt_topic)
    #print("wait message from topic: " + mqtt_topic)
    #module.waitUnsolicited("+QMTRECV:", 60)
    #module.unsubscribeFromMqttTopic(mqtt_topic)

    module.sendATcmd("AT+QMTDISC=0", "+QMTDISC:", 10)
    module.closeConnection()
    module.deactivatePdpContext(contextID, 5)

module.close()




