
#import signal
#import sys
import time
# from ftplib import FTP
# from ast import literal_eval
# import xml.etree.ElementTree as ET
#import datetime
#from random import randint
#import subprocess
#import numpy as np
from db_helper import db_helper
from rules import rules
from weather_forecast import weather_forecast




while True:

    # reset classes to allow initialised vars to be changed without restart

weather_forecast = weather_forecast()
db_helper = db_helper()
rules = rules()

# Get data
weather_forecast.get_forecast()


# check data
forecast_current = weather_forecast.check_forecast_current()

# Extract precipitation info
min_precip = weather_forecast.get_min_precip()
prob_precip = weather_forecast.get_prob_precip()

min_precip_0 = min_precip[0]
min_precip_1 = min_precip[1]
prob_precip_0 = prob_precip[0]
prob_precip_1 = prob_precip[1]

# Calc time since last water
hours_since_last_water = db_helper.get_last_water()

# Calc average moisture L12H
av_moisture_L12H = db_helper.get_av_water()

## Override rules
# Watered recently
watered_recently_override = rules.watered_recently(hours_since_last_water)

# high soil moisture
moisture_override = rules.moisture(av_moisture_L12H)

# rain expected
rain_override = rules.rain(min_precip, prob_precip, forecast_current)

# collate rules
hold_watering = rules.collate_rules(moisture_override, rain_override, watered_recently_override)


# Insert results
insert_stmt = """
                INSERT INTO watering_rules (
                forecast_current,
                min_precip_0,
                prob_precip_0,
                min_precip_1,
                prob_precip_1,
                min_precip_threshold,
                min_precip_prob_threshold,
                time_since_last_water,
                min_hours_between_watering,
                av_moisture_L12H,
                min_moisture_threshold,
                rain_override,
                watered_recently_override,
                moisture_override,
                hold_watering)
                VALUES
                ({},{},{},{},{},{},{},{},{},{},{},{},{},{},{})""".format(
                    forecast_current,
                    min_precip_0,
                    prob_precip_0,
                    min_precip_1,
                    prob_precip_1,
                    rules.min_precip_threshold,
                    rules.min_precip_prob_threshold,
                    hours_since_last_water,
                    rules.min_hours_between_watering,
                    av_moisture_L12H,
                    rules.min_moisture_threshold,
                    rain_override,
                    watered_recently_override,
                    moisture_override,
                    hold_watering
                )

db_helper.insert_data(insert_stmt)

    time.sleep(10800)



