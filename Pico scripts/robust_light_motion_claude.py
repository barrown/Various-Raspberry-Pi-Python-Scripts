import uasyncio as asyncio
from machine import Pin, ADC, reset
from time import sleep
import network
import urequests
from json import dumps
import gc

# Wi-Fi credentials
SSID = "YOUR-SSID"
PASSWORD = "YOUR-PASSWORD"

headers = {"Authorization": "Bearer REPLACE-WITH-YOU-TOKEN",
           "content-type": "application/json"}

average_light = 42.0  # start somewhere in the middle of the range so it's quicker to settle
motion = True
wifi_connected = False

# Network configuration
HASS_IP = "192.168.0.104"
HASS_PORT = "8123"
WEBHOOK_ID = "-8VTNUcKdt1ugGVGsLn4LrEf4"
REQUEST_TIMEOUT = 10  # seconds

def safe_http_request(method, url, headers=None, data=None, timeout=REQUEST_TIMEOUT):
    """Make HTTP request with proper error handling and cleanup"""
    response = None
    try:
        if method.upper() == "POST":
            response = urequests.post(url, headers=headers, data=data, timeout=timeout)
        elif method.upper() == "PUT":
            response = urequests.put(url, headers=headers, data=data, timeout=timeout)
        
        if response:
            # Check if request was successful
            if 200 <= response.status_code < 300:
                return True
            else:
                #print(f"HTTP request failed with status: {response.status_code}")
                return False
    except Exception as e:
        #print(f"HTTP request error: {e}")
        return False
    finally:
        if response:
            response.close()
        # Force garbage collection to prevent memory leaks
        gc.collect()
    
    return False

async def connect_to_wifi():
    """Async Wi-Fi connection with proper error handling"""
    global wifi_connected
    wlan = network.WLAN(network.STA_IF)
    
    try:
        wlan.active(True)
        await asyncio.sleep(1)  # Give time for interface to activate
        
        if not wlan.isconnected():
            print(f"Connecting to WiFi: {SSID}")
            wlan.connect(SSID, PASSWORD)
            
            # Wait for connection with timeout
            max_attempts = 30  # 30 seconds timeout
            attempts = 0
            
            while not wlan.isconnected() and attempts < max_attempts:
                await asyncio.sleep(1)
                attempts += 1
            
            if wlan.isconnected():
                wifi_connected = True
                #print("WiFi connected:", wlan.ifconfig())
                return True
            else:
                wifi_connected = False
                #print("WiFi connection failed - timeout")
                return False
        else:
            wifi_connected = True
            return True
            
    except Exception as e:
        #print(f"WiFi connection error: {e}")
        wifi_connected = False
        return False

def setstate(lux):
    """Send light level to Home Assistant with error handling"""
    if not wifi_connected:
        return False
        
    data = dumps({
        "state": lux,
        "attributes": {
            "unit_of_measurement": "lx",
            "friendly_name": "Light level",
            "device_class": "illuminance",
            "state_class": "measurement"
        }
    })
    
    url = f"http://{HASS_IP}:{HASS_PORT}/api/states/sensor.lightlevel"
    return safe_http_request("POST", url, headers=headers, data=data)

async def maintain_wifi_connection():
    """Asynchronous task to maintain Wi-Fi connection"""
    global wifi_connected
    
    # Initial connection
    await connect_to_wifi()
    
    while True:
        try:
            wlan = network.WLAN(network.STA_IF)
            
            # Check if we're still connected
            if not wlan.isconnected():
                wifi_connected = False
                #print("WiFi connection lost, attempting to reconnect...")
                
                # Try to reconnect
                success = await connect_to_wifi()
                if not success:
                    # If reconnection fails, wait longer before trying again
                    await asyncio.sleep(30)
                    continue
            else:
                wifi_connected = True
            
            # Regular check interval
            await asyncio.sleep(15)
            
        except Exception as e:
            #print(f"WiFi maintenance error: {e}")
            wifi_connected = False
            await asyncio.sleep(30)

async def measure_light():
    """Measure light levels with error handling"""
    global average_light
    
    try:
        # Define pin for our sensor
        lightsensor = ADC(Pin(26))
        NUM_AVG = 100
        lightlist = [0] * NUM_AVG
        
        while True:
            try:
                await asyncio.sleep(0.1)
                
                # Remove first value
                del lightlist[0]
                
                # Read sensor value, turn it into a percentage, round to 1 decimal
                light = round((lightsensor.read_u16()) / 65535 * 100, 1)
                
                # Stick light value to the end of the list
                lightlist.append(light)
                
                # Communicate average light value to other tasks
                average_light = round(sum(lightlist) / NUM_AVG, 1)
                
            except Exception as e:
                #print(f"Light measurement error: {e}")
                await asyncio.sleep(1)
                
    except Exception as e:
        #print(f"Light sensor initialization error: {e}")
        # If sensor fails, use a default value
        average_light = 42.0

async def detect_motion():
    """Detect motion with error handling"""
    global motion
    
    try:
        pir = Pin(27, Pin.IN, Pin.PULL_DOWN)
        await asyncio.sleep(10)  # Delay to allow the sensor to settle
        
        while True:
            try:
                await asyncio.sleep(0.05)
                motion = pir.value() == 1
                
            except Exception as e:
                #print(f"Motion detection error: {e}")
                await asyncio.sleep(1)
                
    except Exception as e:
        #print(f"Motion sensor initialization error: {e}")
        # If sensor fails, assume no motion
        motion = False

async def trigger_webhook():
    """Trigger webhook with robust error handling"""
    global average_light, motion
    
    no_motion_countdown = 0
    await asyncio.sleep(20)  # Wait for sensors to become ready
    
    webhook_url = f"http://{HASS_IP}:{HASS_PORT}/api/webhook/{WEBHOOK_ID}"
    webhook_headers = {"Content-Type": "application/json"}
    
    while True:
        try:
            await asyncio.sleep(0.1)
            
            if not wifi_connected:
                await asyncio.sleep(5)  # Wait if no WiFi
                continue
            
            if motion and average_light < 50 and no_motion_countdown < 1:
                data = dumps({"state": "on"})
                success = safe_http_request("PUT", webhook_url, headers=webhook_headers, data=data)
                
                if success:
                    #print("Light turned ON")
                    no_motion_countdown = 3000  # Reset countdown timer
                else:
                    #print("Failed to turn light ON")
                    pass
                    
            elif motion:  # Just motion but it's not dark or counter not at zero yet
                no_motion_countdown = 3000  # Reset countdown timer
                
            else:  # No motion
                no_motion_countdown -= 1  # Subtract one from the countdown
                
                if no_motion_countdown == 0:  # Timer hits zero
                    data = dumps({"state": "off"})
                    success = safe_http_request("PUT", webhook_url, headers=webhook_headers, data=data)
                    
                    if success:
                        #print("Light turned OFF")
                        pass
                    else:
                        #print("Failed to turn light OFF")
                        pass
                        
        except Exception as e:
            print(f"Webhook trigger error: {e}")
            await asyncio.sleep(5)

async def update_hass():
    """Update Home Assistant with light levels"""
    global average_light
    
    while True:
        try:
            await asyncio.sleep(30)
            
            if wifi_connected:
                success = setstate(average_light)
                if success:
                    #print(f"Updated HASS with light level: {average_light}")
                    pass
                else:
                    #print(f"Failed to update HASS with light level: {average_light}")
                    pass
            else:
                #print("Skipping HASS update - no WiFi")
                pass
                
        except Exception as e:
            #print(f"HASS update error: {e}")
            await asyncio.sleep(30)

async def memory_management():
    """Periodic memory cleanup"""
    while True:
        try:
            await asyncio.sleep(60)  # Run every minute
            gc.collect()
            # Optionally print free memory for debugging
            #print(f"Free memory: {gc.mem_free()}")
        except Exception as e:
            #print(f"Memory management error: {e}")
            pass

async def watchdog():
    """System watchdog - reset if too many errors occur"""
    error_count = 0
    max_errors = 50  # Reset after 50 errors
    
    while True:
        try:
            await asyncio.sleep(300)  # Check every 5 minutes
            
            # Reset error count if we made it this far without issues
            if error_count > 0:
                error_count -= 1
                
        except Exception as e:
            #print(f"Watchdog error: {e}")
            error_count += 1
            
            if error_count >= max_errors:
                #print("Too many errors - resetting system...")
                await asyncio.sleep(5)
                reset()

# Main function to run all tasks concurrently
async def main():
    """Main function with comprehensive error handling"""
    try:
        # Start all tasks
        tasks = [
            measure_light(),
            detect_motion(),
            trigger_webhook(),
            update_hass(),
            maintain_wifi_connection(),
            memory_management(),
            watchdog()
        ]
        
        await asyncio.gather(*tasks)
        
    except Exception as e:
        #print(f"Critical system error: {e}")
        #print("Restarting system in 10 seconds...")
        await asyncio.sleep(10)
        reset()

# Initialize and run
if __name__ == "__main__":
    #print("Starting robust light and motion sensor...")
    try:
        asyncio.run(main())
    except Exception as e:
        #print(f"Unhandled exception: {e}")
        #print("System will restart in 10 seconds...")
        sleep(10)
        reset()