#v1.0

import time, unicornhat
from math import floor

unicornhat.set_layout(unicornhat.AUTO) # can be HAT, PHAT, PHAT_VERTICAL or AUTO, this script works for HAT
unicornhat.rotation(0) # Specify the rotation in degrees: 0, 90, 180 or 270
unicornhat.brightness(0.9) # Set the display brightness between 0.0 and 1.0

#dictionary of times to pixels
pixels = {900:{'x':(0,2),'y':(0,3)},
          1000:{'x':(2,4),'y':(0,3)},
          1100:{'x':(4,6),'y':(0,3)},
          1200:{'x':(6,8),'y':(0,3)},
          1300:{'x':(0,2),'y':(3,6)},
          1400:{'x':(2,4),'y':(3,6)},
          1500:{'x':(4,6),'y':(3,6)},
          1600:{'x':(6,8),'y':(3,6)},
          1700:{'x':(0,2),'y':(6,8)},
          0:{'x':(2,3),'y':(6,7)},
          5:{'x':(3,4),'y':(6,7)},
          10:{'x':(4,5),'y':(6,7)},
          15:{'x':(5,6),'y':(6,7)},
          20:{'x':(6,7),'y':(6,7)},
          25:{'x':(7,8),'y':(6,7)},
          30:{'x':(2,3),'y':(7,8)},
          35:{'x':(3,4),'y':(7,8)},
          40:{'x':(4,5),'y':(7,8)},
          45:{'x':(5,6),'y':(7,8)},
          50:{'x':(6,7),'y':(7,8)},
          55:{'x':(7,8),'y':(7,8)}}

#def for setting the relevant pixels to the relevant colours, whether its hour or minute
def setcolour(clock, r, g, b):
    for x in range(pixels[clock]['x'][0],pixels[clock]['x'][1]):
        for y in range(pixels[clock]['y'][0],pixels[clock]['y'][1]):
            unicornhat.set_pixel(x, y, r, g, b)


# run through all pixels on startup
for clock in pixels:
    unicornhat.clear()
    setcolour(clock, 0, 255, 0)
    unicornhat.show()
    time.sleep(0.1)
unicornhat.clear()
time.sleep(1)


while True:
    unicornhat.clear()
    hour = int(time.strftime('%H00'))
    minute = int(time.strftime('%M'))
    fiveminute = 5 * floor(minute/5)
    
    if hour < 700 or hour > 2059:
        # just the minutes in dim red, so we know the pi is still working
        setcolour(fiveminute, 64, 0, 0)
    elif hour < 900 or hour > 1759 or minute == 59:
        # set all to dim red - I shouldn't been at the desk
        unicornhat.set_all(64, 0, 0)
    elif hour == 1200:
        # red 12 and red minutes
        setcolour(hour, 255, 0, 0)
        setcolour(fiveminute, 255, 0, 0)
    else:
        if minute == 0: # hour and minute to green
            setcolour(hour, 0, 255, 0)
            setcolour(fiveminute, 0, 255, 0)
        else: # otherwise set the colours to be white
            setcolour(hour, 255, 255, 255)
            setcolour(fiveminute, 255, 255, 255)

    unicornhat.show()
    time.sleep(5)