#! python3
# v2.3

# modules for speedtest and HA
from time import sleep
from json import loads, dumps
import subprocess
import requests

# modules for influx
from datetime import datetime
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import ASYNCHRONOUS
from urllib3 import Retry

# metadata for influxdb
retries = Retry(total=10, backoff_factor=0.5)
url = 'http://192.168.0.103:8086'
org = '8294c5278e68feb7'
token = 'REPLACE-WITH-YOU-TOKEN'
bucket = 'home_assistant'

# metadata for home assistant
headers = {"Authorization": "Bearer REPLACE-WITH-YOU-TOKEN",
           "content-type": "application/json"}
rootstates = 'http://192.168.0.104:8123/api/states/sensor.'


sleep(30) # let the system settle after a restart/reboot before running the speedtest

while True:
    # Send webhook to HA to turn off Deluge temporarily
    requests.put("http://192.168.0.104:8123/api/webhook/-deluge")
    sleep(10) # wait for Deluge to settle down

    # run speedtest
    speedtest = subprocess.run(['speedtest', '--accept-license', '--accept-gdpr', '-f', 'json'], capture_output=True)

    if speedtest.returncode == 0:
        data = loads(speedtest.stdout)
    else:
        #print('speedtest fail',data)
        sleep(30)
        continue

    # write to home assistant
    payload=dumps({"state": data['ping']['jitter'], "attributes": {"unit_of_measurement": "ms",
                                                 "friendly_name": "Jitter",
                                                 "device_class": "duration",
                                                 "state_class": "measurement"}})
    requests.post(rootstates+'speedtestjitter', headers=headers, data=payload)


    payload=dumps({"state": data['ping']['latency'], "attributes": {"unit_of_measurement": "ms",
                                                 "friendly_name": "Ping Speedtest",
                                                 "device_class": "duration",
                                                 "state_class": "measurement"}})
    requests.post(rootstates+'speedtestping', headers=headers, data=payload)


    payload=dumps({"state": data['upload']['bandwidth']/125000, "attributes": {"unit_of_measurement": "MiB/s",
                                                 "friendly_name": "Upload",
                                                 "device_class": "data_rate",
                                                 "state_class": "measurement"}})
    requests.post(rootstates+'speedtestupload', headers=headers, data=payload)


    payload=dumps({"state": data['download']['bandwidth']/125000, "attributes": {"unit_of_measurement": "MiB/s",
                                                 "friendly_name": "Download",
                                                 "device_class": "data_rate",
                                                 "state_class": "measurement"}})
    requests.post(rootstates+'speedtestdownload', headers=headers, data=payload)


    payload=dumps({"state": data.get('packetLoss', 0.0), "attributes": {"unit_of_measurement": "%",
                                                 "friendly_name": "Packet Loss",
                                                 "state_class": "measurement"}})
    requests.post(rootstates+'speedtestpacketloss', headers=headers, data=payload)

    # sometimes the URL isn't present
    try:
        payload=dumps({"state": data['result']['url']+'.png', "attributes": {"friendly_name": "Speedtest Image URL"}})
        requests.post(rootstates+'speedtesturl', headers=headers, data=payload)
    except:
        pass

    # write data to influxdb
    client = InfluxDBClient(url=url, token=token, org=org, retries=retries)
    write_api = client.write_api(write_options=ASYNCHRONOUS)

    p1 = Point('ms').tag('speedtest', 'jitter').field('jitter', float(data['ping']['jitter'])).time(data['timestamp'], write_precision='s')
    p2 = Point('ms').tag('speedtest', 'ping').field('latency', float(data['ping']['latency'])).time(data['timestamp'], write_precision='s')
    p3 = Point('MBps').tag('speedtest', 'download').field('download', round(data['download']['bandwidth']/125000, 2)).time(data['timestamp'], write_precision='s')
    p4 = Point('MBps').tag('speedtest', 'upload').field('upload', round(data['upload']['bandwidth']/125000, 2)).time(data['timestamp'], write_precision='s')
    p5 = Point('%').tag('speedtest', 'packetloss').field('packetloss', float(data.get('packetLoss', 0.0))).time(data['timestamp'], write_precision='s')
    p6 = Point('server').tag('speedtest', 'server').field('id', data['server']['id']).field('location', data['server']['location']).field('host', data['server']['host']).field('name', data['server']['name']).time(data['timestamp'], write_precision='s')

    write_api.write(bucket=bucket, record=[p1, p2, p3, p4, p5, p6])

    write_api.__del__()
    client.__del__()

    sleep(5000)
