#!/usr/local/bin/python3.11
# This is for Unicorn HAT on a Pi Zero, which has Python 3.11 compiled on it especially
# v1.2


# Use aiohttp and asyncio to handle the websockets connection
import asyncio
from aiohttp import ClientSession

# Third party library which contains the functions/classes to talk to HA
from hass_client import HomeAssistantClient

# set up unicorn HAT 
import unicornhat
unicornhat.set_layout(unicornhat.HAT)
unicornhat.rotation(0) # Specify the rotation in degrees: 0, 90, 180 or 270
unicornhat.brightness(0.9) # Set the display brightness between 0.0 and 1.0

# function to convert between hue and RGB
from colorsys import hsv_to_rgb

# these have to match the entity names in Home Assistant
list_of_entities = ["sensor.lightlevel",
                    "sensor.solar_power",
                    "sensor.modbus_grid_power",
                    "sensor.solaredge_i1_dc_voltage",
                    "sensor.speedtestdownload",
                    "sensor.speedtestupload",
                    "sensor.011927b884ad", # = outside temp
                    "sensor.011927dd1fad", # = top of tank temp
                    "sensor.eee895_pressure",
                    "sensor.eee895_co2",
                    "sensor.co2_change_over_10_minutes",
                    "remote.sony_tv",
                    "sensor.kid_s_tablet_battery_level",
                    "sensor.aircraft_tracked_with_location",
                    "update.pi_hole_core_update_available",
                    "update.pi_hole_web_update_available",
                    "update.pi_hole_ftl_update_available",
                    "update.home_assistant_supervisor_update",
                    "update.home_assistant_core_update",
                    "update.home_assistant_operating_system_update",
                    "sensor.backup_state",
                    "update.octopus_energy_update",
                    "update.solaredge_modbus_multi_update",
                    "update.hildebrand_glow_dcc_update",
                    "update.waste_collection_schedule_update",
                    "update.mini_graph_card_update",
                    "update.sun_card_update",
                    "update.hacs_update",
                    "sensor.deluge_up_speed",
                    "sensor.pihole_load_15m",
                    "sensor.rpi4_load_15m",
                    "sensor.pizero_load_15m",
                    "sensor.influxssd_load_15m",
                    "sensor.load_15m",
                    "sensor.unicorn_load_15m",
                    "sensor.camzero2_load_15m",
                    "sensor.co2_load_15m",
                    "sensor.inky_sensors_inky_load_15m",
                    "sensor.radio_sensors_radio_load_15m",
                    "sensor.rpi5_sensors_rpi5_load_15m",
                    "sensor.sdr_sensors_sdr_load_15m"]

# Different entities have different pixel(s) on the Unicorn, so assign each entity to a location
dict_of_entities = {'solar_power':{'x':(0,2),'y':(0,2)},
                    'modbus_grid_power':{'x':(2,4),'y':(0,2)},
                    'solaredge_i1_dc_voltage':{'x':(4,6),'y':(0,2)},
                    'speedtestdownload':{'x':(6,7),'y':(0,2)},
                    'speedtestupload':{'x':(7,8),'y':(0,2)},
                    '011927b884ad':{'x':(0,2),'y':(2,4)}, # outside
                    '011927dd1fad':{'x':(2,4),'y':(2,4)}, # top of tank
                    'eee895_pressure':{'x':(4,6),'y':(2,4)},
                    'eee895_co2':{'x':(6,7),'y':(2,4)},
                    'co2_change_over_10_minutes':{'x':(7,8),'y':(2,4)},
                    'sony_tv':{'x':(0,2),'y':(4,6)},
                    'kid_s_tablet_battery_level':{'x':(2,4),'y':(4,6)},
                    'aircraft_tracked_with_location':{'x':(4,6),'y':(4,6)},
                    'home_assistant':{'x':(6,7),'y':(4,5)},
                    'hacs':{'x':(7,8),'y':(4,5)},
                    'pi_hole':{'x':(6,7),'y':(5,6)},
                    'backup_state':{'x':(7,8),'y':(5,6)},
                    'deluge_up_speed':{'x':(0,2),'y':(6,8)},
                    'pihole_load_15m':{'x':(2,3),'y':(6,7)},
                    'rpi4_load_15m':{'x':(3,4),'y':(6,7)},
                    'pizero_load_15m':{'x':(4,5),'y':(6,7)},
                    'influxssd_load_15m':{'x':(5,6),'y':(6,7)},
                    'load_15m':{'x':(6,7),'y':(6,7)}, # HA load
                    'unicorn_load_15m':{'x':(7,8),'y':(6,7)},
                    'camzero2_load_15m':{'x':(2,3),'y':(7,8)},
                    'co2_load_15m':{'x':(3,4),'y':(7,8)},
                    'inky_sensors_inky_load_15m':{'x':(4,5),'y':(7,8)},
                    'radio_sensors_radio_load_15m':{'x':(5,6),'y':(7,8)},
                    'rpi5_sensors_rpi5_load_15m':{'x':(6,7),'y':(7,8)},
                    'sdr_sensors_sdr_load_15m':{'x':(7,8),'y':(7,8)}}

# Can't have a value less than 110, else with unicorn.brightness = 0.4, it doesn't illuminate
RED = (255,0,0)
ORANGE = (255,128,0)
YELLOW = (255,255,0)
DIMGREEN = (0,110,0)
GREEN = (0,255,0)
CYAN = (0,255,255)
BLUE = (0,0,255)
PURPLE = (128,0,255)
WHITE = (255,255,255)
OFF = (0,0,0)

def fadeup(value, old_max=20, new_min=110, new_max=255) -> int:
    """Scales a value from its range (0 to old_max) to another, such as 110 to 255"""
    # Three sensors have max value of 20, so make that the default
    # RGB range is limited to 110--255 so limit min/max to those values
    return int(min(max((value / old_max) * (new_max - new_min) + new_min, 110), 255))

# As there are ~8 Pis with identical profiles, a single function makes sense
def rgb_for_pi_load(state) -> tuple:
    '''
    <20 = DIMGREEN
    >50 = RED
    20-50 = ORANGE
    Unavailable/offline = PURPLE
    '''
    value = handle_float_state(state)
    
    if value == -12345678.9:
        return PURPLE
    elif value < 20:
        return DIMGREEN
    elif value > 50:
        return RED
    else:
        return ORANGE
    
# This is where we tell the unicorn which LEDs to light up, based on the mapping dictionary
def setcolour(entity, r, g, b) -> None:
    """Take an entity (str) and RGB values (int 0-255) and show it on the unicorn HAT"""
    for x in range(dict_of_entities[entity]['x'][0], dict_of_entities[entity]['x'][1]):
        for y in range(dict_of_entities[entity]['y'][0], dict_of_entities[entity]['y'][1]):
            unicornhat.set_pixel(x, y, r, g, b)
    unicornhat.show()


def handle_float_state(state: str) -> float:
    """Take the raw string from Home Assistant and convert to a float that won't break the downstream function."""
    try:
        # most of the time the state will be a number that we want to return
        state = float(state)
        return state
    except ValueError:
        # sometimes the value is a string as the sensor isn't ready or offline
        # send back a magic float for each function to handle
        if state == "unavailable" or state == "unknown":
            return -12345678.9
        else:
            print("Something has gone really wrong, I'm getting a state of", state)
            return 0




def setcolour_solar_power(state):
    '''
    0 kW = Purple
    <0.5 kW = Blue
    0.5 kW-2.2 kW = Dim Green
    2.2-3.5 kW = Bright Green
    > 3.5 kW = White
    '''
    value = handle_float_state(state)
    if value == -12345678.9:
        r, g, b = OFF
    elif value == 0:
        r, g, b, = PURPLE
    elif value < 0.5:
        r, g, b, = BLUE
    elif value < 2.2:
        r, g, b, = DIMGREEN
    elif value < 3.5:
        r, g, b, = GREEN
    else:
        r, g, b, = WHITE

    setcolour('solar_power', r, g, b)


def setcolour_modbus_grid_power(state):
    '''
    <-0.1 kW = Cyan
    -0.1-0.1 = Green
    0.1-1 = Orange
    >1 = Red
    '''
    value = handle_float_state(state)
    if value == -12345678.9:
        r, g, b = OFF
    elif value < 0.1 and value > -0.1: # around zero
        r, g, b = GREEN
    elif value < 0: # exporting
        r, g, b = CYAN
    else: # importing
        r, g, b = PURPLE
        
    setcolour("modbus_grid_power", r, g, b)


def setcolour_solaredge_i1_dc_voltage(state):
    '''
    0 = Purple
    >0-350 = Dim Green
    >350 = Green
    '''
    value = handle_float_state(state)
    if value == -12345678.9:
        r, g, b = OFF
    elif value == 0:
        r, g, b, = PURPLE
    elif value < 350:
        r, g, b, = YELLOW
    else:
        r, g, b, = GREEN

    setcolour('solaredge_i1_dc_voltage', r, g, b)


# def setcolour_hydro_power_gen_1(state):
#     '''
#     <0.1 = ORANGE
#     0.1-20 = GREEN fades up from 110 to 255
#     '''
#     value = handle_float_state(state)
#     
#     if value == -12345678.9:
#         r, g, b = OFF
#     elif value < 0.1:
#         r, g, b, = YELLOW
#     else:
#         r, g, b, = (0, fadeup(value), 0)
#         
#     setcolour('hydro_power_gen_1', r, g, b)


def setcolour_speedtestupload(state):
    '''
    <80 = RED
    <100 = ORANGE
    >100 = GREEN
    '''
    value = handle_float_state(state)
    
    if value == -12345678.9:
        r, g, b = OFF
    elif value < 80:
        r, g, b = RED
    elif value < 100:
        r, g, b = ORANGE
    else:
        r, g, b = GREEN

    setcolour('speedtestupload', r, g, b)


def setcolour_speedtestdownload(state):
    '''
    <800 = RED
    <900 = ORANGE
    >900 = GREEN
    '''
    value = handle_float_state(state)
    
    if value == -12345678.9:
        r, g, b = OFF
    elif value < 800:
        r, g, b = RED
    elif value < 900:
        r, g, b = ORANGE
    else:
        r, g, b = GREEN

    setcolour('speedtestdownload', r, g, b)
    
    
def setcolour_011927b884ad(state):
    '''
    <2 = Blue
    linear hsv map between blue and green
    >15 = Green
    '''
    value = handle_float_state(state)
    
    if value == -12345678.9:
        r, g, b = OFF
    else:
        hue = 240 - min(max(int(120*(value-2)/13),0),120) # green is 120 (temp > 15), blue is 240 (temp < 2)
        r, g, b = [int(c * 255) for c in hsv_to_rgb(hue/360, 1.0, 1.0)]
        
    setcolour('011927b884ad', r, g, b)


def setcolour_011927dd1fad(state):
    '''
    <37 = Red
    linear hsv map between red and green
    >44 = Green
    '''
    value = handle_float_state(state)
    
    if value == -12345678.9:
        r, g, b = OFF
    else:
        hue = min(max(int(120*(value-37)/7),0),120) # green is 120 (temp > 44), red is 0 (temp < 37)
        r, g, b = [int(c * 255) for c in hsv_to_rgb(hue/360, 1.0, 1.0)]
    
    setcolour('011927dd1fad', r, g, b)


def setcolour_eee895_pressure(state):
    '''
    <900 = RED
    <1000 = ORANGE
    <1010 = GREEN
    <1020 = CYAN
    >1020 = PURPLE
    '''
    value = handle_float_state(state)
    
    if value == -12345678.9:
        r, g, b = OFF
    elif value < 900:
        r, g, b = RED
    elif value < 1000:
        r, g, b = ORANGE
    elif value < 1010:
        r, g, b = GREEN
    elif value < 1020:
        r, g, b = CYAN
    else:
        r, g, b = PURPLE

    setcolour('eee895_pressure', r, g, b)


def setcolour_eee895_co2(state):
    '''
    <800 = GREEN
    <1500 = YELLOW
    >1500 = RED
    '''
    value = handle_float_state(state)
    
    if value == -12345678.9:
        r, g, b = OFF
    elif value < 800:
        r, g, b = GREEN
    elif value < 1500:
        r, g, b = YELLOW
    else:
        r, g, b = RED
    
    setcolour('eee895_co2', r, g, b)


def setcolour_co2_change_over_10_minutes(state):
    '''
    <-40 = CYAN      : CO2 levels dropping fast
    >40 = ORANGE     : CO2 levels rising fast
    -40-40 = GREEN   : Stable CO2
    '''
    value = handle_float_state(state)
    
    if value == -12345678.9:
        r, g, b = OFF
    elif value <-40:
        r, g, b = CYAN
    elif value > 40:
        r, g, b = ORANGE
    else:
        r, g, b = GREEN
        
    setcolour('co2_change_over_10_minutes', r, g, b)


def setcolour_sony_tv(state):
    '''
    on = YELLOW
    unavailable = PURPLE
    off = PURPLE
    '''

    if state == "on":
        r, g, b = YELLOW
    else: # state == "unavailable" or state == "unknown":
        r, g, b = PURPLE

    setcolour('sony_tv', r, g, b)


def setcolour_kid_s_tablet_battery_level(state):
    '''
    <20 = RED
    >50 = GREEN
    20-50 = ORANGE
    '''
    value = handle_float_state(state)
    
    if value == -12345678.9:
        r, g, b = OFF
    elif value < 20:
        r, g, b = RED
    elif value > 50:
        r, g, b = GREEN
    else:
        r, g, b = ORANGE
        
    setcolour('kid_s_tablet_battery_level', r, g, b)


def setcolour_aircraft_tracked_with_location(state):
    '''
    0 = PURPLE
    >20 = YELLOW
    0-20 = Fadeup cyan from 110 to 255
    '''
    value = handle_float_state(state)
    
    if value == -12345678.9:
        r, g, b = OFF
    elif value == 0:
        r, g, b = PURPLE
    elif value > 20:
        r, g, b = YELLOW
    else:
        r, g, b, = (0, fadeup(value), fadeup(value))

    setcolour('aircraft_tracked_with_location', r, g, b)


def setcolour_pi_hole(state):
    '''
    off = DIMGREEN
    else = ORANGE
    '''
    if state == "off":
        r, g, b = DIMGREEN
    else:
        r, g, b = ORANGE
        
    setcolour('pi_hole', r, g, b)


def setcolour_home_assistant(state):
    '''
    off = DIMGREEN
    else = ORANGE
    '''
    if state == "off":
        r, g, b = DIMGREEN
    else:
        r, g, b = ORANGE
        
    setcolour('home_assistant', r, g, b)


def setcolour_backup_state(state):
    '''
    backed_up = DIMGREEN
    else = ORANGE
    '''
    if state == "backed_up":
        r, g, b = DIMGREEN
    else:
        r, g, b = ORANGE
        
    setcolour('backup_state', r, g, b)


def setcolour_hacs(state):
    '''
    off = DIMGREEN
    else = ORANGE
    '''
    if state == "off":
        r, g, b = DIMGREEN
    else:
        r, g, b = ORANGE
        
    setcolour('hacs', r, g, b)


def setcolour_deluge_up_speed(state):
    '''
    >6000 = YELLOW
    <100 = PURPLE
    100-2000 = Fadeup green
    '''
    value = handle_float_state(state)
    
    if value == -12345678.9:
        r, g, b = OFF
    elif value < 100:
        r, g, b = PURPLE
    elif value > 6000:
        r, g, b = YELLOW
    else:
        r, g, b, = (0, fadeup(value, 2000), 0)  # use second argument in fadeup() to specific max
        
    setcolour('deluge_up_speed', r, g, b)


def setcolour_pihole_load_15m(state):
    '''
    <20 = DIMGREEN
    >50 = RED
    20-50 = ORANGE
    '''
    r, g, b = rgb_for_pi_load(state)
    setcolour('pihole_load_15m', r, g, b)


def setcolour_rpi4_load_15m(state):
    '''
    <20 = DIMGREEN
    >50 = RED
    20-50 = ORANGE
    '''
    r, g, b = rgb_for_pi_load(state)
    setcolour('rpi4_load_15m', r, g, b)


def setcolour_pizero_load_15m(state):
    '''
    <20 = DIMGREEN
    >50 = RED
    20-50 = ORANGE
    '''
    r, g, b = rgb_for_pi_load(state)
    setcolour('pizero_load_15m', r, g, b)


def setcolour_influxssd_load_15m(state):
    '''
    <20 = DIMGREEN
    >50 = RED
    20-50 = ORANGE
    '''
    r, g, b = rgb_for_pi_load(state)
    setcolour('influxssd_load_15m', r, g, b)


def setcolour_load_15m(state):
    '''
    Unlike other loads that range 0-100, this is 0-1
    <0.4 = DIMGREEN
    >1 = RED
    0.4-1 = ORANGE
    '''
    value = handle_float_state(state)
    
    if value == -12345678.9:
        r, g, b = OFF
    elif value < 0.4:
        r, g, b = DIMGREEN
    elif value > 1:
        r, g, b = RED
    else:
        r, g, b = ORANGE

    setcolour('load_15m', r, g, b)


def setcolour_unicorn_load_15m(state):
    '''
    <20 = DIMGREEN
    >50 = RED
    20-50 = ORANGE
    '''
    r, g, b = rgb_for_pi_load(state)
    setcolour('unicorn_load_15m', r, g, b)


def setcolour_camzero2_load_15m(state):
    '''
    <20 = DIMGREEN
    >50 = RED
    20-50 = ORANGE
    '''
    r, g, b = rgb_for_pi_load(state)
    setcolour('camzero2_load_15m', r, g, b)


def setcolour_co2_load_15m(state):
    '''
    <20 = DIMGREEN
    >50 = RED
    20-50 = ORANGE
    '''
    r, g, b = rgb_for_pi_load(state)
    setcolour('co2_load_15m', r, g, b)


def setcolour_inky_sensors_inky_load_15m(state):
    '''
    <20 = DIMGREEN
    >50 = RED
    20-50 = ORANGE
    '''
    r, g, b = rgb_for_pi_load(state)
    setcolour('inky_sensors_inky_load_15m', r, g, b)


def setcolour_radio_sensors_radio_load_15m(state):
    '''
    <20 = DIMGREEN
    >50 = RED
    20-50 = ORANGE
    '''
    r, g, b = rgb_for_pi_load(state)
    setcolour('radio_sensors_radio_load_15m', r, g, b)


def setcolour_rpi5_sensors_rpi5_load_15m(state):
    '''
    <20 = DIMGREEN
    >50 = RED
    20-50 = ORANGE
    '''
    r, g, b = rgb_for_pi_load(state)
    setcolour('rpi5_sensors_rpi5_load_15m', r, g, b)


def setcolour_sdr_sensors_sdr_load_15m(state):
    '''
    <20 = RED # pager pipeline isn't running!
    >50 = ORANGE
    20-50 = DIMGREEN
    '''
    value = handle_float_state(state)
    
    if value == -12345678.9:
        r, g, b = PURPLE
    elif value < 20:
        r, g, b = RED
    elif value > 50:
        r, g, b = ORANGE
    else:
        r, g, b = DIMGREEN
    setcolour('sdr_sensors_sdr_load_15m', r, g, b)



# # The first message contains all entries and looks like this:
# {'a': {'update.home_assistant_supervisor_update': {'s': 'off', 'a': {'auto_update': True, 'display_precision': 0, 'installed_version': '2024.11.2', 'in_progress': False, 'latest_version': '2024.11.2', 'release_summary': None, 'release_url': 'https://github.com/home-assistant/supervisor/releases/tag/2024.11.2', 'skipped_version': None, 'title': 'Home Assistant Supervisor', 'update_percentage': None, 'entity_picture': 'https://brands.home-assistant.io/hassio/icon.png', 'friendly_name': 'Home Assistant Supervisor Update', 'supported_features': 1},
#        'sensor.011927dd1fad': {'s': '49.969', 'a': {'unit_of_measurement': '°C', 'friendly_name': 'Top of Tank', 'device_class': 'temperature', 'state_class': 'measurement'}, 'c': {'id': '01JCJ5QSW8SK4PPZ9HVS2R2W6Z', 'parent_id': None, 'user_id': '81c9e42d29b54ab59870e2a5d509143b'}, 'lc': 1731481823.1128883},
#        'sensor.011927b884ad': {'s': '7.937', 'a': {'unit_of_measurement': '°C', 'friendly_name': 'Outside', 'device_class': 'temperature', 'state_class': 'measurement'}, 'c': {'id': '01JCJ65QJS964N7BP69QX08QTC', 'parent_id': None, 'user_id': '81c9e42d29b54ab59870e2a5d509143b'}, 'lc': 1731482279.5130875}}}}
# # The state change messages look like this:
# {'c': {'sensor.011927b884ad': {'+': {'s': '8.0', 'lc': 1731482306.8424184, 'c': '01JCJ66J8TSGSCDQTNPVGM51NS'}}}}
# {'c': {'sensor.load_15m': {'+': {'s': '0.21', 'lc': 1731482307.5276923, 'c': '01JCJ66JY7KXYN0S8S2E9NXF1K'}}}}

def parse_statechange(statechange) -> None:
    match statechange:
        case {'c': {'sensor.lightlevel': {'+': {'s': state}}}}:
            # set the brightness of the UnicornHAT to between 0.4 and 0.9
            # according to the outside lightlevel (which ranges 0-100)
            unicornhat.brightness(0.4 + (max(handle_float_state(state),0) / 100.0) * 0.5)
        case {'c': {'sensor.solar_power': {'+': {'s': state}}}}:
            setcolour_solar_power(state)
        case {'c': {'sensor.modbus_grid_power': {'+': {'s': state}}}}:
            setcolour_modbus_grid_power(state)
        case {'c': {'sensor.solaredge_i1_dc_voltage': {'+': {'s': state}}}}:
            setcolour_solaredge_i1_dc_voltage(state)
        case {'c': {'sensor.speedtestupload': {'+': {'s': state}}}}:
            setcolour_speedtestupload(state)
        case {'c': {'sensor.speedtestdownload': {'+': {'s': state}}}}:
            setcolour_speedtestdownload(state)
        case {'c': {'sensor.011927b884ad': {'+': {'s': state}}}}:
            setcolour_011927b884ad(state)
        case {'c': {'sensor.011927dd1fad': {'+': {'s': state}}}}:
            setcolour_011927dd1fad(state)
        case {'c': {'sensor.eee895_pressure': {'+': {'s': state}}}}:
            setcolour_eee895_pressure(state)
        case {'c': {'sensor.eee895_co2': {'+': {'s': state}}}}:
            setcolour_eee895_co2(state)
        case {'c': {'sensor.co2_change_over_10_minutes': {'+': {'s': state}}}}:
            setcolour_co2_change_over_10_minutes(state)
        case {'c': {'remote.sony_tv': {'+': {'s': state}}}}:
            setcolour_sony_tv(state)
        case {'c': {'sensor.kid_s_tablet_battery_level': {'+': {'s': state}}}}:
            setcolour_kid_s_tablet_battery_level(state)
        case {'c': {'sensor.aircraft_tracked_with_location': {'+': {'s': state}}}}:
            setcolour_aircraft_tracked_with_location(state)
        case {'c': {'sensor.backup_state': {'+': {'s': state}}}}:
            setcolour_backup_state(state)
                    
        case {'c': {'update.pi_hole_core_update_available': {'+': {'s': state}}}} | {'c': {'update.pi_hole_web_update_available': {'+': {'s': state}}}} | {'c': {'update.pi_hole_ftl_update_available': {'+': {'s': state}}}}:
            setcolour_pi_hole(state)

        case {'c': {'update.home_assistant_supervisor_update': {'+': {'s': state}}}} | {'c': {'update.home_assistant_core_update': {'+': {'s': state}}}} | {'c': {'update.home_assistant_operating_system_update': {'+': {'s': state}}}} :
            setcolour_home_assistant(state)

        case {'c': {'update.octopus_energy_update': {'+': {'s': state}}}} | {'c': {'update.solaredge_modbus_multi_update': {'+': {'s': state}}}} | {'c': {'update.hildebrand_glow_dcc_update': {'+': {'s': state}}}} | {'c': {'update.waste_collection_schedule_update': {'+': {'s': state}}}} | {'c': {'update.mini_graph_card_update': {'+': {'s': state}}}} | {'c': {'update.sun_card_update': {'+': {'s': state}}}} | {'c': {'update.hacs_update': {'+': {'s': state}}}}:
            setcolour_hacs(state)

        case {'c': {'sensor.deluge_up_speed': {'+': {'s': state}}}}:
            setcolour_deluge_up_speed(state)
        case {'c': {'sensor.pihole_load_15m': {'+': {'s': state}}}}:
            setcolour_pihole_load_15m(state)
        case {'c': {'sensor.rpi4_load_15m': {'+': {'s': state}}}}:
            setcolour_rpi4_load_15m(state)
        case {'c': {'sensor.pizero_load_15m': {'+': {'s': state}}}}:
            setcolour_pizero_load_15m(state)
        case {'c': {'sensor.influxssd_load_15m': {'+': {'s': state}}}}:
            setcolour_influxssd_load_15m(state)
        case {'c': {'sensor.load_15m': {'+': {'s': state}}}}:
            setcolour_load_15m(state)
        case {'c': {'sensor.unicorn_load_15m': {'+': {'s': state}}}}:
            setcolour_unicorn_load_15m(state)
        case {'c': {'sensor.camzero2_load_15m': {'+': {'s': state}}}}:
            setcolour_camzero2_load_15m(state)
        case {'c': {'sensor.co2_load_15m': {'+': {'s': state}}}}:
            setcolour_co2_load_15m(state)
        case {'c': {'sensor.inky_sensors_inky_load_15m': {'+': {'s': state}}}}:
            setcolour_inky_sensors_inky_load_15m(state)
        case {'c': {'sensor.radio_sensors_radio_load_15m': {'+': {'s': state}}}}:
            setcolour_radio_sensors_radio_load_15m(state)
        case {'c': {'sensor.rpi5_sensors_rpi5_load_15m': {'+': {'s': state}}}}:
            setcolour_rpi5_sensors_rpi5_load_15m(state)
        case {'c': {'sensor.sdr_sensors_sdr_load_15m': {'+': {'s': state}}}}:
            setcolour_sdr_sensors_sdr_load_15m(state)
        case _ :
            # This catches 'a' (all) entities when we first connect, defaulting to an empty dictionary if 'a' is not there
            # which happens when an attribute changes, but not a value, which we silently ignore
            # e.g. {'c': {'remote.sony_tv': {'+': {'lu': 1731571836.9029186, 'c': '01JCMVJSZ667X5JFT63X8T58QX', 'a': {'current_activity': 'com.sony.dtv.tvx'}}}}}
            # {'c': {'sensor.co2_change_over_10_minutes': {'+': {'lu': 1731574109.1933641, 'c': '01JCMXR509QS5JHKTMDW1YZ61R', 'a': {'age_coverage_ratio': 0.8}}}}}
            # grab the key for each entity and call the right function
            for key in statechange.get('a',{}):
                #print(key, statechange['a'][key]['s'])
                if key == 'sensor.lightlevel':
                    unicornhat.brightness(0.4 + (max(handle_float_state(statechange['a'][key]['s']),0) / 100.0) * 0.5)
                elif key == 'sensor.solar_power':
                    setcolour_solar_power(statechange['a'][key]['s'])
                elif key == 'sensor.modbus_grid_power':
                    setcolour_modbus_grid_power(statechange['a'][key]['s'])
                elif key == 'sensor.solaredge_i1_dc_voltage':
                    setcolour_solaredge_i1_dc_voltage(statechange['a'][key]['s'])
                elif key == 'sensor.speedtestupload':
                    setcolour_speedtestupload(statechange['a'][key]['s'])
                elif key == 'sensor.speedtestdownload':
                    setcolour_speedtestdownload(statechange['a'][key]['s'])
                elif key == 'sensor.011927b884ad':
                    setcolour_011927b884ad(statechange['a'][key]['s'])
                elif key == 'sensor.011927dd1fad':
                    setcolour_011927dd1fad(statechange['a'][key]['s'])
                elif key == 'sensor.eee895_pressure':
                    setcolour_eee895_pressure(statechange['a'][key]['s'])
                elif key == 'sensor.eee895_co2':
                    setcolour_eee895_co2(statechange['a'][key]['s'])
                elif key == 'sensor.co2_change_over_10_minutes':
                    setcolour_co2_change_over_10_minutes(statechange['a'][key]['s'])
                elif key == 'remote.sony_tv':
                    setcolour_sony_tv(statechange['a'][key]['s'])
                elif key == 'sensor.kid_s_tablet_battery_level':
                    setcolour_kid_s_tablet_battery_level(statechange['a'][key]['s'])
                elif key == 'sensor.aircraft_tracked_with_location':
                    setcolour_aircraft_tracked_with_location(statechange['a'][key]['s'])
                elif key == 'sensor.backup_state':
                    setcolour_backup_state(statechange['a'][key]['s'])
                
                elif key == 'update.pi_hole_core_update_available' or key == 'update.pi_hole_web_update_available' or key == 'update.pi_hole_ftl_update_available':
                    setcolour_pi_hole(statechange['a'][key]['s'])
                
                elif key == 'update.home_assistant_supervisor_update' or key == 'update.home_assistant_core_update' or key == 'update.home_assistant_operating_system_update':
                    setcolour_home_assistant(statechange['a'][key]['s'])
                
                elif key == 'update.octopus_energy_update' or key == 'update.solaredge_modbus_multi_update' or key == 'update.hildebrand_glow_dcc_update' or key == 'update.waste_collection_schedule_update' or key == 'update.mini_graph_card_update' or key == 'update.sun_card_update' or key == 'update.hacs_update':
                    setcolour_hacs(statechange['a'][key]['s'])
                
                elif key == 'sensor.deluge_up_speed':
                    setcolour_deluge_up_speed(statechange['a'][key]['s'])
                elif key == 'sensor.pihole_load_15m':
                    setcolour_pihole_load_15m(statechange['a'][key]['s'])
                elif key == 'sensor.pizero_load_15m':
                    setcolour_pizero_load_15m(statechange['a'][key]['s'])
                elif key == 'sensor.rpi4_load_15m':
                    setcolour_rpi4_load_15m(statechange['a'][key]['s'])
                elif key == 'sensor.pizero_load_15m':
                    setcolour_pizero_load_15m(statechange['a'][key]['s'])
                elif key == 'sensor.influxssd_load_15m':
                    setcolour_influxssd_load_15m(statechange['a'][key]['s'])
                elif key == 'sensor.load_15m':
                    setcolour_load_15m(statechange['a'][key]['s'])
                elif key == 'sensor.unicorn_load_15m':
                    setcolour_unicorn_load_15m(statechange['a'][key]['s'])
                elif key == 'sensor.camzero2_load_15m':
                    setcolour_camzero2_load_15m(statechange['a'][key]['s'])
                elif key == 'sensor.co2_load_15m':
                    setcolour_co2_load_15m(statechange['a'][key]['s'])
                elif key == 'sensor.inky_sensors_inky_load_15m':
                    setcolour_inky_sensors_inky_load_15m(statechange['a'][key]['s'])
                elif key == 'sensor.radio_sensors_radio_load_15m':
                    setcolour_radio_sensors_radio_load_15m(statechange['a'][key]['s'])
                elif key == 'sensor.rpi5_sensors_rpi5_load_15m':
                    setcolour_rpi5_sensors_rpi5_load_15m(statechange['a'][key]['s'])
                elif key == 'sensor.sdr_sensors_sdr_load_15m':
                    setcolour_sdr_sensors_sdr_load_15m(statechange['a'][key]['s'])
                else:
                    print("GOT AN UNRECOGNISED KEY!",key)







async def main() -> None:
    """Run main."""
    websocket_url = "ws://192.168.0.104:8123/api/websocket"
    with open("token.txt", "r") as tokenfile:
        token = tokenfile.read()

    # initialise aiohttp session
    async with ClientSession() as session:
        
        # run forever
        while True:
            try:
                # start the client/connect to HA with our credentials
                # this is important if we get disconnected because of a HA restart
                async with HomeAssistantClient(websocket_url, token, session) as client:
                    # subscribe_entities() takes a callback function (parse_statechange) and a list of entities we want to subscribe to
                    # it listens for changes to those events and sends the JSON to the callback function
                    # this will start the function, which keeps running for as long as we're still connected
                    await client.subscribe_entities(parse_statechange, list_of_entities)
                    
                    # Run whilst we still have a connection
                    while client.connected:
                        await asyncio.sleep(30)
                    
                    print("Connection lost")
                    
            except Exception as e:
                # Usually this will be caused by HomeAssistantClient() when trying to connect
                # "Cannot connect to host 192.168.0.104:8123 ssl:default [Connect call failed ('192.168.0.104', 8123)]"
                # whilst we wait for HA to restart
                print(f"Error: {e}")
            
            # Wait before creating new session
            await asyncio.sleep(30)
            
            

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except:
        print("Something bad happened or got a signal to quit.")
        unicornhat.off()
        exit
