
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

BomFtpHost = "ftp2.bom.gov.au"
BomFtpPort = 21
BomFtpForecastPath = "/anon/gen/fwo/"
forecast_id = "IDV10450.xml"


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

ftp = FTP(BomFtpHost)
ftp.login(user='anonymous', passwd='guest')
ftp.cwd(BomFtpForecastPath)

ftp.retrbinary('RETR IDV10450.xml', open('IDV10450.xml', 'wb').write)

ftp.quit()

# Parse xml

tree = ET.parse('IDV10450.xml')  
root = tree.getroot()

issue_time = datetime.datetime.utcnow()
expiry_time = datetime.datetime.utcnow()


for elem in root:
    for subelem in elem:
        if subelem.tag == 'expiry-time':
            expiry_time = datetime.datetime.strptime(subelem.text, '%Y-%m-%dT%H:%M:%SZ')
        if subelem.tag == 'issue-time-utc':
            issue_time = datetime.datetime.strptime(subelem.text, '%Y-%m-%dT%H:%M:%SZ')

        

forecast_current = (issue_time <= datetime.datetime.utcnow() <= expiry_time)

# Get precipitation figures

min_precip_0 = 0
prob_precip_0 = 0
min_precip_1 = 0
prob_precip_1 = 0



for elem in root:
    if elem.tag == 'forecast':
        for subelem in elem:
            if(subelem.attrib['aac'] == 'VIC_PT042'):
                for subelem2 in subelem:
                    if(subelem2.attrib['index'] == '0'):
                        for subelem3 in subelem2:
                            if(subelem3.attrib['type'] == 'precipitation_range'):
                                min_precip_0 = float(subelem3.text.split(' ')[0])
                            if(subelem3.attrib['type'] == 'probability_of_precipitation'):
                                prob_precip_0 = float((subelem3.text.replace('%','')))/100
                    if(subelem2.attrib['index'] == '1'):
                        for subelem3 in subelem2:
                            if(subelem3.attrib['type'] == 'precipitation_range'):
                                min_precip_1 = float(subelem3.text.split(' ')[0])
                            if(subelem3.attrib['type'] == 'probability_of_precipitation'):
                                prob_precip_1 = float((subelem3.text.replace('%','')))/100

                
#Watering logic

hold_watering = False

# Good chance of decent rain today:
if forecast_current == True:
    if prob_precip_0 > 0.6 and min_precip_0 > 5:
        hold_watering = True

# Good chance of decent rain tomorrow:
    if prob_precip_1 > 0.6 and min_precip_1 > 5:
        hold_watering = True


# Last water

query_watering = """
SELECT
ts,
watered
FROM watering
WHERE watered = '1'
ORDER BY ts ASC
"""

con = mariadb.connect(host = db_host, port = db_host_port, user = db_user, password = db_pass, database = db)
cur = con.cursor()

cur.execute(query_watering)

last_water_sql = datetime.datetime.now()

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

if calc_time_since_water(last_water) < 47:
    hold_watering = True

watered = False
duration = 0
# If allowed, trigger relay to run sprinkler for 30 mins

if hold_watering == False:
    start_time = time.time()
    relay.ON_1()
    
    # test
    time.sleep(10)
    
    # prod
    #time.sleep(1800)
    relay.OFF_1()
    end_time = time.time()
    watered = True

    duration = end_time - start_time

# Add record to database

insert_stmt = """
INSERT INTO watering
(watered, duration, forecast_current, min_precip_0, prob_precip_0, min_precip_1, prob_precip_1, hold_watering, time_since_last_water)
VALUES
('{}',{},{},{},{},{},{},{},{})""".format(watered,duration, forecast_current, min_precip_0, prob_precip_0, min_precip_1, prob_precip_1, hold_watering, calc_time_since_water(last_water))

con = mariadb.connect(host = db_host, port = db_host_port, user = db_user, password = db_pass, database = db)
cur = con.cursor()
try:
    cur.execute(insert_stmt)
    con.commit()
except:
    con.rollback()
con.close()

#_________________________________________________________#
############# SET UP DATABASE COLUMNS #####################
#_________________________________________________________#

