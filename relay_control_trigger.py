
import signal
import sys
import time
import smbus
import mysql.connector as mariadb
from ftplib import FTP
from ast import literal_eval
import xml.etree.ElementTree as ET
import datetime
from random import randint

# Set control parameters

watering_duration = randint(300, 1800)
# seconds. Randomly calculate time between 5 and 30 mins, to test duration options

time_since_rules_check = 24 # if latest rules greater than this value, execute exception process
min_moisture_threshold = 2.5  # taken from moisture readings. Average over 12 hours
exception_hours_between_watering = 70

# Set db variables

db_host = 'hda.amahi.net'
db_host_port = '3306'
db_user = 'rpi'
db_pass = 'warm_me'
db = 'soil'

# Initialise variables

hold_watering == True
hours_since_last_rules = 999
watered = False
duration = 0.0

# Relay control

bus = smbus.SMBus(1)  # 0 = /dev/i2c-0 (port I2C0), 1 = /dev/i2c-1 (port I2C1)


class Relay():
    global bus

    def __init__(self):
        # 7 bit address (will be left shifted to add the read write bit)
        self.DEVICE_ADDRESS = 0x20
        self.DEVICE_REG_MODE1 = 0x06
        self.DEVICE_REG_DATA = 0xff
        bus.write_byte_data(self.DEVICE_ADDRESS,
                            self.DEVICE_REG_MODE1, self.DEVICE_REG_DATA)

    def ON_1(self):
        self.DEVICE_REG_DATA &= ~(0x1 << 0)
        bus.write_byte_data(self.DEVICE_ADDRESS,
                            self.DEVICE_REG_MODE1, self.DEVICE_REG_DATA)

    def OFF_1(self):
        self.DEVICE_REG_DATA |= (0x1 << 0)
        bus.write_byte_data(self.DEVICE_ADDRESS,
                            self.DEVICE_REG_MODE1, self.DEVICE_REG_DATA)

    def ALLOFF(self):
        self.DEVICE_REG_DATA |= (0xf << 0)
        bus.write_byte_data(self.DEVICE_ADDRESS,
                            self.DEVICE_REG_MODE1, self.DEVICE_REG_DATA)


relay = Relay()

# Called on process interruption. Set all pins to "Input" default mode.


def endProcess(signalnum=None, handler=None):
    relay.ALLOFF()
    sys.exit()


signal.signal(signal.SIGINT, endProcess)

query_rules = """
SELECT
hold_watering,
TIMESTAMPDIFF(hour,ts,NOW())
FROM watering
order by ts
"""

con = mariadb.connect(host=db_host, port=db_host_port,
                      user=db_user, password=db_pass, database=db)
cur = con.cursor()

cur.execute(query_rules)

for row in cur:
    hold_watering = bool(row[0])
    hours_since_last_rules = row[1]

# Exception

query_exception = """
SELECT
TIMESTAMPDIFF(hour, ts, NOW()),
watered
FROM watering_records
WHERE watered in('1', 'True')
ORDER BY ts ASC
"""
if hours_since_last_rules > time_since_rules_check:

    con = mariadb.connect(host=db_host, port=db_host_port,
    user=db_user, password=db_pass, database=db)

    cur = con.cursor()

    cur.execute(query_exception)

    hours_since_last_water = 999

    for row in cur:
        hours_since_last_water = row[0]

    hold_watering = True

    if hours_since_last_water > exception_hours_between_watering:
        hold_watering = False


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
INSERT INTO watering_records
(watered, duration, hours_since_last_rules)
VALUES
({},{},{})""".format(watered, duration, hours_since_last_rules)

con = mariadb.connect(host=db_host, port=db_host_port,
                      user=db_user, password=db_pass, database=db)
cur = con.cursor()
try:
    cur.execute(insert_stmt)
    con.commit()
except:
    con.rollback()
con.close()
