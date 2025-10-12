import network
from json import loads
from time import sleep
from machine import Pin
from neopixel import NeoPixel
import asyncio

# Network configuration
SSID = "SSID"
PASSWORD = "PASSWORD"


# Neopixel setup
LED_COUNT = 30
strip = NeoPixel(Pin(28, Pin.OUT), LED_COUNT)
# Red wire on VBUS pin 40
# Black wire on GND pin 38
# Green wire on GP28 pin 34

strip.fill((255, 0, 0))
strip.write()


def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(SSID, PASSWORD)
        while not wlan.isconnected():
            sleep(1)


# parse_colour is launched by handle_client()
def parse_colour(payload):
    """
    Parse colour from webhook payload, which will be a JSON object
    curl -X POST http://192.168.0.201/   -H "Content-Type: application/json"   -d '{"colour": [0, 128, 255]}'
    curl -X POST http://192.168.0.201/   -H "Content-Type: application/json"   -d '{"colour": "purple"}'
    """
    try:
        if isinstance(payload.get('colour'), str):
            colour_str = payload['colour']
            if colour_str == "orange":
                colour = (255, 128, 0)
            elif colour_str == "purple":
                colour = (255, 0, 255)
            elif colour_str == "cyan":
                colour = (0, 255, 255)
            elif colour_str == "red":
                colour = (255, 0, 0)
            elif colour_str == "white":
                colour = (255, 255, 255)
            elif colour_str == "off":
                colour = (0, 0, 0)
            else:
                colour = (255, 0, 0)
        
        elif isinstance(payload.get('colour'), list):
            colour_list = payload['colour']
            colour = tuple(int(x) for x in colour_list[:3])
                    
        else:
            print('Invalid colour format in payload')
            colour = (255, 255, 0)  # yellow indicates invalid colour format
        
    except (KeyError, ValueError) as e:
        print('Error parsing colour:', e)
        colour = (255, 0, 0)  # red indicates python exception has occured

    strip.fill(colour)
    strip.write()


        
# handle_client is launched by webhook_server()
async def handle_client(reader, writer):
    try:
        # Read the request line and headers
        request = ''
        while True:
            line = await reader.readline()
            request += line.decode()
            if line == b'\r\n' or not line:
                break
        
        # Parse Content-Length
        content_length = None
        for line in request.split('\r\n'):
            if line.lower().startswith('content-length:'):
                content_length = int(line.split(':')[1].strip())
                break
        
        if content_length:
            # Read the body
            body = await reader.read(content_length)
            
            try:
                webhook_data = loads(body)
                
                # Send payload to other function to update colour
                parse_colour(webhook_data)

                response = 'HTTP/1.1 200 OK\r\nContent-Length: 0\r\n\r\n'
            except ValueError:
                response = 'HTTP/1.1 400 Bad Request\r\nContent-Length: 0\r\n\r\n'
        else:
            response = 'HTTP/1.1 400 Bad Request\r\nContent-Length: 0\r\n\r\n'
        
        writer.write(response.encode())
        await writer.drain()
        
    except Exception as e:
        writer.write(b'HTTP/1.1 500 Internal Server Error\r\nContent-Length: 0\r\n\r\n')
        await writer.drain()
    finally:
        writer.close()
        await writer.wait_closed()


async def webhook_server():
    await asyncio.start_server(handle_client, '0.0.0.0', 80)
    while True:
        await asyncio.sleep(1)  # Keep server running
        


async def main():
    # Connect to WiFi
    connect_wifi()

    strip.fill((0, 255, 0))
    strip.write()
    
    # Create tasks
    server_task = asyncio.create_task(webhook_server())

    # Wait for all tasks indefinitely
    await asyncio.gather(server_task)
    

# Start the event loop
try:
    asyncio.run(main())
except KeyboardInterrupt:
    print('Program terminated by user')