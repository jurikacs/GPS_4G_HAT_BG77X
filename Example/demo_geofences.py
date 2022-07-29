'''
  demo_geofences.py - This is basic Finamon GNSS/4G Modem HAT Shield positioning function example.
'''
import time

import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from Library.BG77X import BG77X


def rect(lat, lon, x, y):
    x = x/2
    y = y/2
    return [(round(lat + x,5), round(lon + y,5)),
            (round(lat + x,5), round(lon - y,5)),
            (round(lat - x,5), round(lon - y,5)),
            (round(lat - x,5), round(lon + y,5))]


geofence_center =  [(51.22906, 6.71467)]

geofence_quad = [
    (51.22916, 6.71459),
    (51.22918, 6.71466),
    (51.22902, 6.71474),
    (51.22900, 6.71468),
    ]

geofence_query = [
    "position unknown",
    "position is inside the geo-fence",
    "position is outside the geo-fence",
    "geo-fence ID does not exist"
    ]


navigator = BG77X()
navigator.gnssOn()
time.sleep(2.)

sleep_time = 10
start_time = time.time()
while(not navigator.acquirePositionInfo()):
    navigator.sendATcmd('AT+QGPSGNMEA="GSV"')
    time.sleep(sleep_time)

print ("position search time %s seconds" % int(time.time() - start_time))

navigator.addGeofence(0, 3, 0, geofence_center, 100)
navigator.sendATcmd('AT+QCFGEXT="addgeo",0')

navigator.addGeofence(3, 3, 3, geofence_quad)
navigator.sendATcmd('AT+QCFGEXT="addgeo",3')

print(geofence_query[navigator.queryGeofence(0)])
print(geofence_query[navigator.queryGeofence(1)])
print(geofence_query[navigator.queryGeofence(3)])

navigator.deleteGeofence(0)
navigator.deleteGeofence(3)

for geoid in range(9):
    navigator.addGeofence(geoid, 3, 0, geofence_center, (geoid + 1) * 5)
    navigator.sendATcmd('AT+QCFGEXT="addgeo",' + str(geoid))

for i in range(10):
    for geoid in range(9):
        print(geofence_query[navigator.queryGeofence(geoid)])
    time.sleep(10.)

navigator.gnssOff()
navigator.close()

