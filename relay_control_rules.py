
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
min_hours_between_watering = 47
min_moisture_threshold = 2.5  # taken from moisture readings. Average over 12 hours

# Location parameters

# Beaumaris
forecast_id = "IDV10450.xml"
location = "VIC_PT042"


# Get BOM forecast xml

BomFtpHost = "ftp2.bom.gov.au"
BomFtpPort = 21
BomFtpForecastPath = "/anon/gen/fwo/"

# Set some parameters

retrieve_string = 'RETR ' + forecast_id


def convert_date(string):
    f = '%Y-%m-%dT%H:%M:%SZ'
    return datetime.datetime.strptime(string, f)


def create_list(index_max):
    list = []
    for item in range(0, index_max):
        list.append(0.0)
    return list


# Get forecast XML

def get_forecast():
    ftp = FTP(BomFtpHost)
    ftp.login(user='anonymous', passwd='guest')
    ftp.cwd(BomFtpForecastPath)
    #ftp.retrlines('LIST')
    ftp.retrbinary(retrieve_string, open(forecast_id, 'wb').write)
    ftp.quit()
    return

    # Parse XML

#############
get_forecast()
############

# Parse xml

def parse_xml(arg):
    tree = ET.parse(arg)
    return tree

#########
tree = parse_xml(forecast_id)
##########

# Check whether forecast message is valid

def check_xml(arg):

    issue_time = convert_date(arg.findtext("amoc/issue-time-utc"))
    expiry_time = convert_date(arg.findtext("amoc/expiry-time"))

    forecast_current = (issue_time <= datetime.datetime.utcnow() <= expiry_time)
    return forecast_current


############
forecast_current = check_xml(tree)
############

# Extract precipitation details

def get_precip():
    min_precip = create_list(index_max)
    prob_precip = create_list(index_max)

    root = tree.getroot()

    for loc in root.iter("area"):
        if loc.attrib['aac'] == location:
            for child in loc:
                for ind in range(0, index_max):
                    if child.attrib['index'] == str(ind):
                        for gc in child:
                            if(gc.attrib['type'] == 'precipitation_range'):
                                min_precip[ind] = float(gc.text.split(' ')[0])
                            if(gc.attrib['type'] == 'probability_of_precipitation'):
                                prob_precip[ind] = float(gc.text.replace('%', ''))/100


    return 
# Determine whether to water based on rain forecast

def check_forecast(min_precip, prob_precip, min_precip_threshold, min_precip_prob_threshold, index_max, forecast_current):
    output = False
    if forecast_current = True:
        for ind in range(0, index_max):
            if prob_precip[ind] > min_precip_prob_threshold and min_precip[ind] > min_precip_threshold:
                output = True
    return output


hold_watering = check_forecast(
    min_precip, prob_precip, min_precip_threshold, min_precip_prob_threshold, index_max, forecast_current)

min_precip_0 = min_precip[0]
min_precip_1 = min_precip[1]
prob_precip_0 = prob_precip[0]
prob_precip_1 = prob_precip[1]

# Last water

query_watering = """
SELECT
TIMESTAMPDIFF(hour,ts,NOW()),
watered
FROM watering_records
WHERE watered in('1', 'True')
ORDER BY ts ASC
"""

con = mariadb.connect(host=db_host, port=db_host_port,
                      user=db_user, password=db_pass, database=db)
cur = con.cursor()

cur.execute(query_watering)

hours_since_last_water = 999

for row in cur:
    hours_since_last_water = row[0]

if hours_since_last_water < min_hours_between_watering:
    hold_watering = True

# check average moisture

query_moisture_1 = """
SELECT
avg(reading)
FROM soil_moisture
WHERE ts > DATE_SUB(now(), INTERVAL 12 HOUR)
"""

con = mariadb.connect(host=db_host, port=db_host_port,
                      user=db_user, password=db_pass, database=db)
cur = con.cursor()

cur.execute(query_moisture_1)

for row in cur:
    av_moisture_L12H = row[0]

if av_moisture_L12H > min_moisture_threshold:
    hold_watering = True


# Add record to database

insert_stmt = """
INSERT INTO watering_rules
(forecast_current, min_precip_0, prob_precip_0, min_precip_1, prob_precip_1, hold_watering, time_since_last_water, av_moisture_L12H)
VALUES
({},{},{},{},{},{},{},{})""".format(forecast_current, min_precip_0, prob_precip_0, min_precip_1, prob_precip_1, hold_watering, hours_since_last_water, av_moisture_L12H)

con = mariadb.connect(host=db_host, port=db_host_port,
                      user=db_user, password=db_pass, database=db)
cur = con.cursor()
try:
    cur.execute(insert_stmt)
    con.commit()
except:
    con.rollback()
con.close()

time.sleep(10800)
