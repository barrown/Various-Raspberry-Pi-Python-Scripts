#! python3
# v2

import unicornhat
from time import sleep, time
import json
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

unicornhat.set_layout(unicornhat.PHAT)
# TOP-RIGHT = 0,0
# BOTTOM-LEFT = 7,3
unicornhat.brightness(0.7)
unicornhat.clear()
unicornhat.show()

online = False

while not online:
    try:
        r = requests.get('http://192.168.0.104:4357')
        if r.status_code == 200:
            online = True
    except:
        unicornhat.set_all(186,218,85) # BADA55
        unicornhat.show()
        sleep(1)
        continue

retries = Retry(total=10, backoff_factor=1)
adapter = HTTPAdapter(max_retries=retries)
http = requests.Session()
http.mount("http://", adapter)

headers = {"Authorization": "Bearer REPLACE-WITH-YOU-TOKEN",
           "content-type": "application/json"}

rootstates = 'http://192.168.0.104:8123/api/states/'

def getstate(sensorname):
    response = http.get(rootstates+sensorname, headers=headers)
    textdict = json.loads(response.text)
    return float(textdict['state'])


while True:
    try:
        unicornhat.clear()
        
        temperature = getstate('sensor.011927b884ad') # outside temp
        inverterstatus = getstate('sensor.inverter_status') # current operational mode of inverter
        solarpower = getstate('sensor.solar_power') # current solar power generated
        gridpower = getstate('sensor.modbus_grid_power') # current grid power
        selfconsumption = getstate('sensor.self_consumption_energy') # daily self-consumption



        ## TEMPERATURE PIXEL (0, 0) = top-right
        if temperature < 10:
            unicornhat.set_pixel(0, 0, 0, 0, 139) # Blue
        elif temperature > 16:
            unicornhat.set_pixel(0, 0, 255, 165, 0) # Orange
        else:
            unicornhat.set_pixel(0, 0, 64, 224, 208) # Turquoise
        unicornhat.show()



        # SOLAR POWER
        solar_dots = int(7.99 - (solarpower / 0.4))
        if solar_dots < -1: solar_dots = -1
        if solar_dots > 7: solar_dots = 7
        if solarpower > 2.3:
            solarcolour = (255, 255, 0) # yellow
        else:
            solarcolour = (168, 0, 168) # purple (can't use 128 as there's not enough voltage to light the dimmest blend)

        for dots in range(8,solar_dots,-1):
            unicornhat.set_pixel(dots, 3, solarcolour) # 3 = left column

        # special blended dot with expanded range for the transitions so they stand out
        solar_modulo = (((solarpower / 0.4)) % 1)/2.5 + 0.4
        unicornhat.set_pixel(solar_dots, 3, tuple([int(x * solar_modulo) for x in solarcolour]))

        if solarpower > 3.1: # really sunny, full yellow
            for dots in range(8):
                unicornhat.set_pixel(dots, 3, solarcolour)
        unicornhat.show()


        #INVERTER STATUS
        if inverterstatus == 5: # clipping
            for dots in range(8):
                unicornhat.set_pixel(dots, 3, 255, 255, 255) # white

        if inverterstatus == 2: # asleep
            for dots in range(8):
                unicornhat.set_pixel(dots, 3, 0, 0, 128) # blue
        unicornhat.show()


        #GRIDPOWER
        if gridpower < 0.1 and gridpower > -0.1:
            for dots in range(3,5):
                unicornhat.set_pixel(dots, 2, 0, 168, 0) # two green dots in the middle
        elif gridpower < 0: # export
            grid_dots = int(0.01 + (gridpower / 0.5)) + 7
            if grid_dots < -1: grid_dots = -1
            if grid_dots > 7: grid_dots = 7
            gridcolour = (0, 255, 255) # cyan
            
            for dots in range(8,grid_dots,-1):
                unicornhat.set_pixel(dots, 2, gridcolour) # middle left column

            # special blended dot with expanded range (0-1 maps to 0.3-0.7) for the transitions so they stand out
            grid_modulo = ((gridpower / 0.5) % 1)/-2.5 + 0.72
            unicornhat.set_pixel(grid_dots, 2, tuple([int(x * grid_modulo) for x in gridcolour]))

        else: #import
            grid_dots = int(7.99 - (gridpower / 0.5))
            if grid_dots < -1: grid_dots = -1
            if grid_dots > 7: grid_dots = 7
            gridcolour = (255, 0, 0) # red
            
            for dots in range(8,grid_dots,-1):
                    unicornhat.set_pixel(dots, 2, gridcolour) # middle left column

            # special blended dot with expanded range (0-1 maps to 0.3-0.7) for the transitions so they stand out
            grid_modulo = (((gridpower / 0.5)) % 1)/2.5 + 0.4
            unicornhat.set_pixel(grid_dots, 2, tuple([int(x * grid_modulo) for x in gridcolour]))
        unicornhat.show()


        #SELF CONSUMPTION
        selfconsumption_dots = int(7.99 - (selfconsumption / 2))
        if selfconsumption_dots < -1: selfconsumption_dots = -1
        if selfconsumption_dots > 7: selfconsumption_dots = 7

        for dots in range(8,selfconsumption_dots,-1):
            unicornhat.set_pixel(dots, 1, 0, 255, 0) # 1 = middle right column, green

        # special blended dot with expanded range for the transitions so they stand out
        selfconsumption_modulo = (((selfconsumption / 2)) % 1)/2.5 + 0.4
        unicornhat.set_pixel(selfconsumption_dots, 1, 0, int(255 * selfconsumption_modulo), 0)

        if selfconsumption >= 16: # max consumption, full green
            for dots in range(8):
                unicornhat.set_pixel(dots, 1, 0, 255, 0)
        unicornhat.show()


        #RAIN CHANCE
        with open('weather_data.csv', 'r', newline='\n') as csvfile:
            list_of_lines = csvfile.readlines()
            
        newest_api_time = float(list_of_lines[0].strip().split(',')[0]) # get the time of the first datapoint (should be close to current time)

        if newest_api_time - time() > 4000: # data is over an hour old
            for dots in range(7):
                unicornhat.set_pixel(7-dots, 0, 255, 0, 0) # red
        else:
            for line in list_of_lines:
                apitime, pop, description, hoursahead = line.strip().split(',')
                dot = 7-int(hoursahead)
                unicornhat.set_pixel(dot, 0, int(float(pop) * 128), 0, int(32 + float(pop) * 196)) # 0 = right column, blue > purple > red on severity
        unicornhat.show()
        
        sleep(60)
        
    except:
        unicornhat.set_all(186,218,85) # BADA55
        unicornhat.show()
        sleep(10)
        continue