#!/usr/bin/python
# v2.7.0

from glob import glob
from time import sleep
from datetime import datetime
import os
from gpiozero import PWMLED
import requests
from json import dumps
import subprocess

sleep(20) #  after a reboot, give the kernel a chance to detect the 1-wire sensors

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
        
        
def calibrate_sensor(unique_sensor_id,temp):
    if unique_sensor_id == '0119278a76fa': # red 1
        temp = temp - 0.141
    elif unique_sensor_id == '011927dba794': # red 3
        temp = temp + 0.281
    elif unique_sensor_id == '011927dc2d4e': # red 4
        temp = temp - 0.234
    elif unique_sensor_id == '011927dd1fad': # red 5
        temp = temp + 0.094
    else:
        temp = temp
    
    return temp

def setstate(sensorname,temperature):
    data=dumps({"state": temperature, "attributes": {"unit_of_measurement": "°C",
                                                     "friendly_name": names[sensorname],
                                                     "device_class": "temperature",
                                                     "state_class": "measurement"}})
    requests.post(rootstates+sensorname, headers=headers, data=data)

names = {'01192789f2e7': 'Boiler Out',
         '0119277223c1': 'Return Flow',
         '00000a71a6f4': 'Garage',
         '011927b884ad': 'Outside'}
headers = {"Authorization": "Bearer REPLACE-WITH-YOU-TOKEN",
           "content-type": "application/json"}
rootstates = 'http://192.168.0.104:8123/api/states/sensor.'

blueled = PWMLED(27)
device_folder = glob('/sys/bus/w1/devices/28-*/hwmon/hwmon[0-9]')
device_folder.sort()
sensors_attached = len(device_folder)
print(sensors_attached,"sensors found:",device_folder)
root_dir = '/home/pi/ftp/files/rpi4/'
list_of_temps = [[0] for sensor in range(sensors_attached)] # start with a zero value in case the first measurement is >100

while True:
    currentdate = datetime.now().strftime('%Y-%m-%d')
    fname = root_dir+'temperature_'+currentdate+'.csv'
    
    if not os.path.isfile(fname):
        with open(fname, 'w') as f:
            f.write('DateTime')
            for sensor_path in device_folder:
                f.write(','+sensor_path.split('/')[5][-12:])
            f.write('\n')

    # read all the temperatures from the devices, store them in a list
    for i, sensor_path in enumerate(device_folder):
        with open(sensor_path + '/temp1_input', 'r') as f:
            lines = f.readlines()

        temp_c = float(lines[0]) / 1000.0
        
#         temp_c = calibrate_sensor(sensor_path.split('/')[5][-12:],temp_c)

        if temp_c > 100 or temp_c < -10:
            print(datetime.now().strftime('%H:%M:%S'),"sensor",sensor_path.split('/')[5],"fault:",temp_c)
            temp_c = list_of_temps[i][-1] # sets the current temp to the last recorded temp in the list
        
        list_of_temps[i].append(temp_c)
    
    # write out the time and temperature to a single CSV
    with open(fname, 'a') as f:
        f.write(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        for i, sensor_path in enumerate(device_folder):
            try:
                setstate(sensor_path.split('/')[5][-12:],list_of_temps[i][-1])
            except:
                pass
            f.write(',{:.3f}'.format(list_of_temps[i][-1]))
            del list_of_temps[i][0] # remove the oldest temp in the list
        f.write('\n')
        os.sync()
    
    # wait 10 seconds between readings, show script is running by fading LED
    for ledbrightness in range(100,0,-1):
        blueled.value = ledbrightness/100.0
        sleep(0.1)
