# Various Raspberry Pi Python Scripts
A collection of python scripts I've coded over the years, mostly here as a backup but maybe of use to others



## CO2 Logging EE895
This runs on a Raspberry Pi Zero 2W under my desk with the excellent [EE895 CO2 Sensor]([url](https://pi3g.com/products/rpi-co2-sens-precision-long-term-calibrated-co2-sensor)) that uses a NDIR dual-beam method, which compensates for aging effects with its auto-calibration, is very insensitive to contamination and offers excellent long-term stability. Every 60 seconds the CO2 and air pressure readings are measured via i2c, logged locally into daily text files, and sent to Home Assistant. On startup the script checks timedatectl and only starts logging once the clock is synchronised.



## Home Assistant Unicorn HAT Websockets
Using a 8x8 RGB [Unicorn HAT]([url](https://shop.pimoroni.com/products/unicorn-hat)) attached to a Raspberry Pi Zero W the state of various sensors can be visualised on my desk.

![Unicorn HAT](https://github.com/barrown/Various-Raspberry-Pi-Python-Scripts/blob/main/Home%20Assistant%20Unicorn%20HAT%20Websockets/2024-12-05%2021.53.38.jpg)
![Unicorn HAT](https://github.com/barrown/Various-Raspberry-Pi-Python-Scripts/blob/main/Home%20Assistant%20Unicorn%20HAT%20Websockets/2025-02-23%2010.15.29.jpg)

To provide diffusion and separate out the different LEDs I made a stand-off from card. There is just a printed piece of paper that is stuck on with magnets to indicate which LEDs correspond to which sensors. This build needs Python 3.11 or later because I used Python's MATCH...CASE logic to parse the Home Assistant state data. The clever Home Assistant Websockets integration is handled by [hass_client]([hass_clhass_clientient](https://github.com/music-assistant/python-hass-client/tree/main/hass_client)). What's nice about Home Assistant and Web Sockets is that the first time you connect it sends you the state of every sensor, and after that it only sends you the updated sensor when it changes, so it's an instant update and doesn't need to be excessively polled. Some sensors are fixed colours depending on status, and others fade brightness or hue depending on the value. Because of aiohttp and async functions, this script is very robust to Home Assistant reboots or unavailability.



## Inky pHAT bindays
Using a Black/Red/White [eInk display]([url](https://shop.pimoroni.com/products/inky-phat?variant=55694721057147)) on a Raspberry Pi Zero W in a [transparent case]([url](https://thepihut.com/products/abs-transparent-case-for-raspberry-pi-zero-zero-w)) I get a daily update of how many days until a bin collection, either recycling or rubbish.

![Bin days](https://github.com/barrown/Various-Raspberry-Pi-Python-Scripts/blob/main/Inky%20pHAT%20bindays/bindays.jpg)
![Bin days](https://github.com/barrown/Various-Raspberry-Pi-Python-Scripts/blob/main/Inky%20pHAT%20bindays/bindays2.jpg)

Every hour the script checks Home Assistant for the latest status on the waste collection calendar, which is taken directly from the council website. Using the PIL library, some text is overlaid on an image and displayed on the eInk screen.



## Inky pHAT Strava Marathon Tracker
Using the [Strava API]([url](https://medium.com/@lejczak.learn/get-your-strava-activity-data-using-python-2023-%EF%B8%8F-b03b176965d0)) the script checks every couple of minutes (between 9am and 6pm) if there's been a new run. It's also possible to not have polling, and just trigger the script to run from Home Assistant.

![Marathon tracker](https://github.com/barrown/Various-Raspberry-Pi-Python-Scripts/blob/main/Inky%20pHAT%20Strava%20Marathon%20Tracker/Marathon%20Tracker.jpg)

Most of the complexity here was in getting matplotlib to produce a very small graph with the ticks and labels by week number. Pandas made it easy to parse the Strava JSON and group by week. If you wanted to use this yourself you need to hard-code the date you started training and when the marathon is... and change your name of course!



## Pico scripts
soundbar_lightstrip.py controls a Raspberry Pi Pico W connected to an [RGB LED strip]([url](https://thepihut.com/products/flexible-rgb-led-strip-neopixel-ws2812-sk6812-compatible-60-led-meter)) and using CircuitPython runs a webserver that takes a JSON payload from Home Assistant. Depending on the status of a chromecast (Play/Pause/Buffering/Stop) the LEDs light up my soundbar.

robust_light_motion_claude.py was vibe coded by Claude, it controls a Raspberry Pi Pico W and is connected to a PIR motion sensor and a photo resistor. It reports the light level (a 10 second average of 100 readings) outside to Home Assistant every 30 seconds. If it's dark and motion is detected it fires off a webhook which turns on a smart light in the room. After 5 minutes of no motion it turns the light off again. Everything is async functions and weird if...else loops with some memory management and a watchdog ... it's not how I would design "embedded" device code! But it works and it is robust!



## POGSAC Pager Parser
This runs on a Raspberry Pi Zero 2W connected to a [USB nooelec SDR]([url](https://www.nooelec.com/store/sdr/sdr-receivers/nesdr-mini-2.html)). Two additional programs are needed: [rtl_fm]([url](https://github.com/AlbrechtL/rtl_fm_streamer)) and [multimon-ng 1.3.1]([url](https://github.com/EliasOenal/multimon-ng)). RTL_FM streams the demodulated radio signals as audio, this is piped to multimon-ng which [decodes the audio]([url](https://www.rtl-sdr.com/rtl-sdr-tutorial-pocsag-pager-decoding)) into individual pager messages, which are piped into my python script. I set up a SQLite3 database with [full text search]([url](https://sqlite.org/fts5.html)) capability to log the messages. The python script uses stdin.readline() to take the standard input from multimon-ng and does a bunch of checks to filter out unwanted messages/noise before logging. To monitor operation, I also send a webhook to Home Assistant whenever a message is received so I know everything is still working.



## Speedtest.net to InfluxDB and Home Assistant
Every 5000 seconds run an internet speedtest and send the results to both Home Assistant and InfluxDB. This runs on a Raspberry Pi 4, which has a gigabit port but is limited to ~940 MBps because of protocol overheads. To get more accurate speeds it also sends a webhook to Home Assistant which suspends the Deluge torrent client running on the same RPi for 60 seconds. Having this long-term data has been very important when raising support issues with Virgin Media over slow degradation of service (week-long time scales).

![Speedtest](https://github.com/barrown/Various-Raspberry-Pi-Python-Scripts/blob/main/Speedtest.net%20to%20InfluxDB%20and%20Home%20Assistant/b99dca56-0b0c-4aee-9deb-d07e0a8f1e6d.png)



## Temperature Logging DS18B20
Two scripts run on both a Raspberry Pi 4 and a Raspbery Pi Zero W with a bunch of [DS18B20 1-wire temperature sensors]([url](https://thepihut.com/blogs/raspberry-pi-tutorials/18095732-sensors-temperature-with-the-1-wire-interface-and-the-ds18b20)). I prefer the neatest of my code to that given in the linked example which has unnecessary lines like `equals_pos = lines[1].find('t=')` ... `temp_string = lines[1][equals_pos+2:]`. On startup the script checks timedatectl and only starts logging once the clock is synchronised. One problem is that if the power goes out, that last line in the text file gets corrupted.



## Unicorn HAT Clock
A very simple script made when working from home during lockdown to encourage me not to be at my desk out of hours, take a stretching break every hour and go green on the hour (usually because I had meeting to join). This has since been superseded by the Home Assistant Unicorn HAT Websockets. Before I knew about Websockets this polls Home Assistant every 60 seconds.



## Unicorn pHAT Solar Display from Home Assistant
A 4x8 [Unicorn pHAT]([url](https://learn.pimoroni.com/article/getting-started-with-unicorn-phat)) running on a Raspberry Pi 4. The first column is solar power generated, turning from purple to yellow once there's enough sun to turn on the dishwasher! The second column is grid power, which is red for importing and cyan for exporting. The third column is daily self-consumption starts at zero and builds up a green bar as the day goes on. The right-hand column is weather. The top-right LED is temperature (orange = warm, cyan = just a coat, blue = gloves and hat) and below that is the chance of precipitation over the next 7 hours, taken from a Open Weather API, via a separate script and saved file.

![pHAT solar](https://github.com/barrown/Various-Raspberry-Pi-Python-Scripts/blob/main/Unicorn%20pHAT%20Solar%20Display%20from%20Home%20Assistant/phatsolar.jpg)

If I was redesigning this I'd have it all as one script with some async functions, and not polling Home Assistant but using the websockets connection.



## Tarot card display on 4-colour e-Ink
A 400x300 4-colour [inky wHAT](https://shop.pimoroni.com/products/inky-what?variant=55696156885371) connected via ribbon cable to a Raspberry Pi 5. Each day two random cards from the major arcana are chosen and some pre-generated interpretations from gen AI are displayed, along with the two cards in pixel art form.

![Tarot display](https://github.com/barrown/Various-Raspberry-Pi-Python-Scripts/blob/main/Tarot%20e-ink/2026-01-05%2012.29.jpg)
