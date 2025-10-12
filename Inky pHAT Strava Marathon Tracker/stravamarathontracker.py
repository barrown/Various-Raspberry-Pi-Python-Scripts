#! python3

import pandas as pd
import requests
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
from matplotlib.dates import MO
import math
from io import BytesIO
from PIL import Image, ImageChops
from datetime import date, datetime, time
from time import sleep
import urllib3
urllib3.disable_warnings()

# imports for inky
from PIL import Image, ImageFont, ImageDraw
from inky.auto import auto
import os

inky_display = auto()
inky_display.set_border(inky_display.WHITE)



payload = {
'client_id': '122106',
'client_secret': 'YOUR-SECRET',
'refresh_token': 'YOUR-TOKEN',
'grant_type': "refresh_token",
'f': 'json'
}

def get_dataset():
    res = requests.post('https://www.strava.com/oauth/token', data=payload, verify=False)
    access_token = res.json()['access_token']
    headers = {'Authorization': f'Authorization: Bearer {access_token}'}
    return requests.get('https://www.strava.com/api/v3/athlete/activities?per_page=200', headers=headers, verify=False).json()

def check_for_new_run():
    df = pd.json_normalize(get_dataset())
    df.start_date_local = pd.to_datetime(df.start_date_local)
    return df.start_date_local[0]

def process_and_plot():
    df = pd.json_normalize(get_dataset())
    df.drop(columns=['map.resource_state','athlete.resource_state','athlete.id','total_photo_count','pr_count','upload_id','kudos_count','achievement_count','id','resource_state','comment_count','athlete_count','photo_count','average_watts','kilojoules','max_heartrate','elev_high','elev_low','workout_type','start_date','has_heartrate','heartrate_opt_out','display_hide_heartrate_option','upload_id_str','external_id','from_accepted_tag','has_kudoed','map.id','map.summary_polyline','utc_offset','private','name','visibility','sport_type','flagged','gear_id','device_watts','end_latlng','start_latlng','timezone','location_city','location_state','location_country','trainer','commute','manual'], inplace=True)
    df.start_date_local = pd.to_datetime(df.start_date_local)
    df.distance = df.distance / 1000
    df.moving_time = df.moving_time / 60
    df = df.loc[df.type == 'Run']
    df = df.loc[df.start_date_local > '2024-12-01']
    df['pace'] = df.moving_time / df.distance
    ten_days_ago = date.today() - pd.Timedelta(days=10)
    mean_pace = df.pace.loc[df.start_date_local >= pd.to_datetime(ten_days_ago, utc=True)].mean()
    distance = df.groupby(pd.Grouper(freq='W-Mon', key='start_date_local', label='left'))['distance'].sum()



    w, h = (inky_display.WIDTH, inky_display.HEIGHT)
    dpi = 144

    fig, (ax,ax2) = plt.subplots(1, 2, figsize=(w/dpi, h/dpi), dpi=dpi)

    ax.plot(distance.index, distance, '.-r', ms=6, lw=1)

    ax.tick_params(axis='y', which='major', direction='inout', labelsize=5)
    ax.tick_params(axis='x', which='both', direction='inout', labelsize=5, labelrotation=90)

    ax.xaxis.set_minor_locator(mdates.WeekdayLocator(byweekday=MO))
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=MO, interval=2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%W'))
    ax.yaxis.set_major_locator(ticker.MultipleLocator(15))
    ax.set_ylim(0, math.ceil(distance.max() / 10) * 10)

    ax.spines["top"].set_linewidth(0.5)
    ax.spines["left"].set_linewidth(0.5)
    ax.spines["right"].set_linewidth(0.5)
    ax.spines["bottom"].set_linewidth(0.5)

    plt.rcParams['text.antialiased'] = False

    ax2.set_axis_off()
    plt.tight_layout()

    with BytesIO() as f:
        fig.savefig(f, dpi=dpi)
        f.seek(0)
        img = Image.open(f).convert('P', palette=(0,1,2))


    img = ImageChops.offset(img, -19, 15)


    PATH = os.path.dirname(__file__)
    fontpath = os.path.join(PATH, "MinecraftRegular.otf")
    bigfont = ImageFont.truetype(fontpath, 16)

    days = str((date(2025,3,23) - date.today()).days)+" days"



    draw = ImageDraw.Draw(img)
    draw.text((1, 0), "Cars 1/2 marathon in", inky_display.BLACK, bigfont)
    draw.text((184, 0), days, inky_display.RED, bigfont)

    percentage = df.distance.sum()/3.60  # 360 km * 100 pixels

    draw.rectangle([5,18,107,30], fill=None, outline=inky_display.BLACK, width=1)
    draw.rectangle([6,19,percentage+6,29], fill=inky_display.RED, outline=inky_display.RED, width=1)

    draw.text((114, 18), "Tot: {:.0f}/360 km".format(df.distance.sum()), inky_display.BLACK, bigfont)
    draw.text((115, 38), "Longest: {:.1f} km".format(df.distance.max()), inky_display.BLACK, bigfont)
    draw.text((115, 60), "Last: ", inky_display.BLACK, bigfont)
    draw.text((162, 60), df.iloc[0].start_date_local.strftime("%d %b"), inky_display.RED, bigfont)
    draw.text((115, 82), "Pace:", inky_display.BLACK, bigfont)
    draw.text((162, 82), "{:.1f} min/km".format(df.iloc[0].pace), inky_display.RED, bigfont)
    draw.text((114, 104), "Trend:", inky_display.BLACK, bigfont)

    x = 175
    y = 103
    avg_pace = df.iloc[0].pace / mean_pace
    if avg_pace > 1.1:
        draw.polygon([(x,y), (x+6,y+12), (x+12,y)], fill=inky_display.RED)
    elif avg_pace < 0.9:
        draw.polygon([(x,y+12), (x+6,y), (x+12,y+12)], fill=inky_display.RED)
    else:
        draw.ellipse((x, y+2, x+10, y+10+2), fill=inky_display.BLACK)




    inky_display.set_image(img)
    inky_display.show()


def is_between_hours(start_hour, end_hour):
    now = datetime.now().time()
    start_time = time(start_hour, 0)
    end_time = time(end_hour, 0)
    return start_time <= now <= end_time

old_run = pd.to_datetime(date(2020,3,23), utc=True)
today = datetime.now().date()
process_and_plot()
exit()

while True:
    if is_between_hours(9, 18):  # Check if current time is between 0900 and 1800
        latest_run = check_for_new_run()
        if latest_run > old_run:
            print("Found a new run that started at",latest_run)
            old_run = latest_run
            process_and_plot()
            sleep(7000)
    elif today != datetime.now().date(): # it's a new day!
        today = datetime.now().date()
        print("It's a new day",today)
        process_and_plot()
        sleep(60*60*8)

    sleep(120)
