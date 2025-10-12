#! python3
# v1

import requests
import json
from time import sleep

url = 'https://api.openweathermap.org/data/3.0/onecall?lat=51.123456&lon=0.123456&exclude=current,minutely,daily,alerts&&units=metric&appid=API-KEY'

response = requests.get(url)
data = json.loads(response.text)
hourly = data["hourly"]

with open('/home/pi/phatsolar/weather_data.csv', 'w') as w:
    for hours_ahead, entry in enumerate(hourly):
        if hours_ahead > 6: break
        #print(hours_ahead, entry['weather'][0]['description'], entry['pop'])
        w.write(str(entry['dt'])+','+str(entry['pop'])+','+entry['weather'][0]['description']+','+str(hours_ahead)+'\n')
