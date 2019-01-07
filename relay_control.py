
import signal
import sys
import time
import smbus
import mysql.connector as mariadb
from ftplib import FTP
from ast import literal_eval
import xml.etree.ElementTree as ET  
import datetime

# Set variables

db_host = 'hda.amahi.net'
db_host_port = '3306'
db_user = 'rpi'
db_pass = 'warm_me'
db = 'soil'

# Set control parameters


index_max = 2  # 1 = rest of day, 2 = tomorrow, so on
min_precip_threshold = 5  # mm expected
min_precip_prob_threshold = 0.6  # % chance of rain
min_hours_between_watering = 71

# Location parameters

# Beaumaris
forecast_id = "IDV10450.xml"
location = "VIC_PT042"


# Relay control

bus = smbus.SMBus(1)  # 0 = /dev/i2c-0 (port I2C0), 1 = /dev/i2c-1 (port I2C1)

class Relay():
    global bus

    def __init__(self):
        self.DEVICE_ADDRESS = 0x20  # 7 bit address (will be left shifted to add the read write bit)
        self.DEVICE_REG_MODE1 = 0x06
        self.DEVICE_REG_DATA = 0xff
        bus.write_byte_data(self.DEVICE_ADDRESS, self.DEVICE_REG_MODE1, self.DEVICE_REG_DATA)

    def ON_1(self):
        self.DEVICE_REG_DATA &= ~(0x1 << 0)
        bus.write_byte_data(self.DEVICE_ADDRESS, self.DEVICE_REG_MODE1, self.DEVICE_REG_DATA)

    def OFF_1(self):
        self.DEVICE_REG_DATA |= (0x1 << 0)
        bus.write_byte_data(self.DEVICE_ADDRESS, self.DEVICE_REG_MODE1, self.DEVICE_REG_DATA)
    
    def ALLOFF(self):
        self.DEVICE_REG_DATA |= (0xf << 0)
        bus.write_byte_data(self.DEVICE_ADDRESS, self.DEVICE_REG_MODE1, self.DEVICE_REG_DATA)

relay = Relay()

    # Called on process interruption. Set all pins to "Input" default mode.
def endProcess(signalnum=None, handler=None):
    relay.ALLOFF()
    sys.exit()


signal.signal(signal.SIGINT, endProcess)

# Get BOM forecast xml

BomFtpHost = "ftp2.bom.gov.au"
BomFtpPort = 21
BomFtpForecastPath = "/anon/gen/fwo/"

# Set some parameters

retrieve_string = 'RETR '+ forecast_id

# Get forecast XML

ftp = FTP(BomFtpHost)
ftp.login(user='anonymous', passwd='guest')
ftp.cwd(BomFtpForecastPath)
#ftp.retrlines('LIST')   
ftp.retrbinary(retrieve_string, open(forecast_id, 'wb').write)
ftp.quit()

# Parse XML

tree = ET.parse(forecast_id)  
root = tree.getroot()

# Check whether forecast message is valid

def convert_date(string):
    f = '%Y-%m-%dT%H:%M:%SZ'
    return datetime.datetime.strptime(string, f)

issue_time = convert_date(tree.findtext("amoc/issue-time-utc"))
expiry_time = convert_date(tree.findtext("amoc/expiry-time"))

forecast_current = (issue_time <= datetime.datetime.utcnow() <= expiry_time)

# Extract precipitation details

def create_list(index_max):
    list = []
    for item in range(0,index_max):
        list.append(0.0)
    return list

min_precip = create_list(index_max)
prob_precip = create_list(index_max)

for loc in root.iter("area"):
    if loc.attrib['aac'] == location:
        for child in loc:
            for ind in range(0,index_max):
                if child.attrib['index'] == str(ind):
                    for gc in child:
                        if(gc.attrib['type'] == 'precipitation_range'):
                            min_precip[ind] = float(gc.text.split(' ')[0])
                        if(gc.attrib['type'] == 'probability_of_precipitation'):
                            prob_precip[ind] = float((gc.text.replace('%','')))/100
                                         

# Determine whether to water based on rain forecast

def check_forecast(min_precip, prob_precip, min_precip_threshold, min_precip_prob_threshold, index_max):
    output = False
    for ind in range(0,index_max):
        if prob_precip[ind] > min_precip_prob_threshold and min_precip[ind] > min_precip_threshold:
                output = True
    return output

hold_watering = check_forecast(min_precip, prob_precip, min_precip_threshold, min_precip_prob_threshold, index_max)

min_precip_0 = min_precip[0]
min_precip_1 = min_precip[1]
prob_precip_0 = prob_precip[0]
prob_precip_1 = prob_precip[1]

# Last water

query_watering = """
SELECT
ts,
watered
FROM watering
WHERE watered in('1', 'True')
ORDER BY ts ASC
"""

con = mariadb.connect(host = db_host, port = db_host_port, user = db_user, password = db_pass, database = db)
cur = con.cursor()

cur.execute(query_watering)

last_water = datetime.datetime.now()

for row in cur:
#    last_water_sql = row[0]
    last_water = row[0]

# test
# last_water = datetime.datetime.now() - datetime.timedelta(days = 4)

#f = '%Y-%m-%d %H:%M:%S'
# last_water = datetime.datetime.strptime(last_water_sql, f)


# prod

def calc_time_since_water(last_water):
    time_since_water = datetime.datetime.now() - last_water
    time_since_water_in_s = time_since_water.total_seconds()
    return divmod(time_since_water_in_s, 3600)[0]

if calc_time_since_water(last_water) < min_hours_between_watering:
    hold_watering = True

watered = False
duration = 0.0
# If allowed, trigger relay to run sprinkler for 30 mins

if hold_watering == False:
    start_time = time.time()
    relay.ON_1()
    
    # test
    # time.sleep(10)
    
    # prod
    time.sleep(1800)
    relay.OFF_1()
    end_time = time.time()
    watered = True

    duration = end_time - start_time

# Add record to database

insert_stmt = """
INSERT INTO watering
(watered, duration, forecast_current, min_precip_0, prob_precip_0, min_precip_1, prob_precip_1, hold_watering, time_since_last_water)
VALUES
({},{},{},{},{},{},{},{},{})""".format(watered,duration, forecast_current, min_precip_0, prob_precip_0, min_precip_1, prob_precip_1, hold_watering, calc_time_since_water(last_water))

con = mariadb.connect(host = db_host, port = db_host_port, user = db_user, password = db_pass, database = db)
cur = con.cursor()
try:
    cur.execute(insert_stmt)
    con.commit()
except:
    con.rollback()
con.close()


