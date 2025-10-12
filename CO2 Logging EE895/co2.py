#!/usr/bin/python
# v1.3

import requests
from json import dumps
from smbus import SMBus
from time import sleep
from datetime import datetime
import os
import subprocess

# settings for CO2 Sensor
EE895ADDRESS = 0x5E
I2CREGISTER = 0x00

# settings for home assistant
headers = {"Authorization": "Bearer REPLACE-WITH-YOU-TOKEN",
           "content-type": "application/json"}
rootstates = 'http://192.168.0.104:8123/api/states/sensor.'

# settings for this script
root_dir = '/home/pi/co2/data/'

# initialise bus
i2cbus = SMBus(1)
sleep(1)

## make sure time is synced correctly before measuring
timesynced = False

while not timesynced:
    subprocess_instance = subprocess.Popen(['timedatectl'], stdout=subprocess.PIPE,
                                           universal_newlines=True)
    cmd_out, _error = subprocess_instance.communicate()
    splitlines = cmd_out.split('\n')
    if splitlines[4][-3:] == 'yes':
        timesynced = True
        print('Time synchronisation achieved.')
    else:
        sleep(1)
        

def setstate(co2,pressure):
    data=dumps({"state": co2, "attributes": {"unit_of_measurement": "ppm",
                                                     "friendly_name": "CO2",
                                                     "device_class": "CO2",
                                                     "state_class": "measurement"}})
    requests.post(rootstates+'eee895_co2', headers=headers, data=data)

    data=dumps({"state": pressure, "attributes": {"unit_of_measurement": "mbar",
                                                     "friendly_name": "CO2 Pressure",
                                                     "device_class": "pressure",
                                                     "state_class": "measurement"}})
    requests.post(rootstates+'eee895_pressure', headers=headers, data=data)


while True:
    currentdate = datetime.now().strftime('%Y-%m-%d')
    fname = root_dir+'co2_'+currentdate+'.csv'
    
    if not os.path.isfile(fname):
        with open(fname, 'w') as f:
            f.write('Datetime,CO2 (ppm),Pressure (mbar)\n')
    
    read_data = i2cbus.read_i2c_block_data(EE895ADDRESS, I2CREGISTER, 8)
    
    co2 = read_data[0].to_bytes(1, 'big') + read_data[1].to_bytes(1, 'big')
    pressure = read_data[6].to_bytes(1, 'big') + read_data[7].to_bytes(1, 'big')

    co2 = int.from_bytes(co2, "big")
    pressure = int.from_bytes(pressure, "big") / 10
    pressure = pressure + 8.45 # offset correction due to sensor calibration

    if pressure > 1080 or pressure < 950 or co2 > 10000 or co2 < 0:
        sleep(15)
        continue
    
    try:
        setstate(co2,pressure)
    except:
        pass

    with open(fname, 'a') as f:
        f.write(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        f.write(',{:.0f},{:.1f}\n'.format(co2,pressure))
        
    sleep(60)
