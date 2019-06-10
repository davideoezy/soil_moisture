
import signal
import sys
import time
from random import randint

from relay import Relay
from db_helper import db_helper

relay = Relay()
db_helper = db_helper()

# Initialise variables

hold_watering = True
watered = False
duration = 0
relay.initialise_relay()


# Set control parameters

parameters = db_helper.get_parameters()
min_duration = parameters[0]
max_duration = parameters[1]
time_since_rules_check = 24 # if latest rules greater than this value, execute exception process
exception_hours_between_watering = parameters[2]


watering_duration = randint(min_duration, max_duration)
# seconds. Randomly calculate time between 5 and 30 mins, to test duration options


# Called on process interruption. Set all pins to "Input" default mode.

watering_check = db_helper.hold_water_check()

hold_watering = bool(int(watering_check[0]))
hours_since_last_rules = watering_check[1]


# Exception

hours_since_last_water = db_helper.get_watered()

if hours_since_last_rules > time_since_rules_check:
    if hours_since_last_water > exception_hours_between_watering:
        hold_watering = False
    else:
        hold_watering = True


# If allowed, trigger relay to run sprinkler for 30 mins

if hold_watering == False:
    start_time = time.time()
    relay.ON_1()
    time.sleep(watering_duration)
    relay.OFF_1()
    end_time = time.time()
    watered = True

    duration = end_time - start_time


# Add record to database

insert_stmt = """
INSERT INTO watering_log
(watered, duration, hours_since_last_rules,  hours_since_last_water)
VALUES
({},{},{},{})""".format(watered, duration, hours_since_last_rules, hours_since_last_water)

db_helper.insert_data(insert_stmt)
