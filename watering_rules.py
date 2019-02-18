
import signal
import sys
import time
import mysql.connector as mariadb
from ftplib import FTP
from ast import literal_eval
import xml.etree.ElementTree as ET
import datetime
from random import randint
import subprocess
import numpy as np


# Set variables

db_host = 'hda.amahi.net'
db_host_port = '3306'
db_user = 'rpi'
db_pass = 'warm_me'
db = 'soil'
wifi_interface = "wlan0"

# Set control parameters


index_max = 2  # 1 = rest of day, 2 = tomorrow, so on
min_precip_threshold = 5  # mm expected
min_precip_prob_threshold = 0.6  # % chance of rain
min_hours_between_watering = 47
min_moisture_threshold = 3.0  # taken from moisture readings. Average over 12 hours

# Location parameters

# Beaumaris
forecast_id = "IDV10450.xml"
location = "VIC_PT042"


# Get BOM forecast xml

BomFtpHost = "ftp2.bom.gov.au"
BomFtpPort = 21
BomFtpForecastPath = "/anon/gen/fwo/"
retrieve_string = 'RETR ' + forecast_id


def read_device_address():
    try:
        proc = subprocess.Popen(["ifconfig", wifi_interface], stdout=subprocess.PIPE, universal_newlines=True)
        out, err = proc.communicate()
        IP = ""
        for line in out.split("\n"):
            if("192.168" in line):
                strings = line.split(" ")
                device_address = strings[9]
                return(device_address)
    except:
        return("ERROR!-ifconfig")


def convert_date(string):
    f = '%Y-%m-%dT%H:%M:%SZ'
    return datetime.datetime.strptime(string, f)


def create_list(index_max):
    listofzeros = [0.0] * index_max
    return listofzeros


# Get forecast XML

def get_forecast():
    ftp = FTP(BomFtpHost)
    ftp.login(user='anonymous', passwd='guest')
    ftp.cwd(BomFtpForecastPath)
    #ftp.retrlines('LIST')
    ftp.retrbinary(retrieve_string, open(forecast_id, 'wb').write)
    ftp.quit()
    return


# Parse xml

def parse_xml(arg):
    tree = ET.parse(arg)
    return tree


# Check whether forecast message is valid

def check_forecast_current(tree):

    issue_time = convert_date(tree.findtext("amoc/issue-time-utc"))
    expiry_time = convert_date(tree.findtext("amoc/expiry-time"))

    forecast_current = (issue_time <= datetime.datetime.utcnow() <= expiry_time)
    return forecast_current

# Extract precipitation details

# minimum forecast precipitation

def get_min_precip(index_max, tree):
    min_precip = create_list(index_max)
    root = tree.getroot()

    for loc in root.iter("area"):
        if loc.attrib['aac'] == location:
            for child in loc:
                for ind in range(0, index_max):
                    if child.attrib['index'] == str(ind):
                        for gc in child:
                            if(gc.attrib['type'] == 'precipitation_range'):
                                min_precip[ind] = np.mean([float(gc.text.split(' ')[0]), float(gc.text.split(' ')[2])])

    return min_precip

# probability of precipitation 

def get_prob_precip(index_max, tree):
    prob_precip = create_list(index_max)

    root = tree.getroot()

    for loc in root.iter("area"):
        if loc.attrib['aac'] == location:
            for child in loc:
                for ind in range(0, index_max):
                    if child.attrib['index'] == str(ind):
                        for gc in child:
                            if(gc.attrib['type'] == 'probability_of_precipitation'):
                                prob_precip[ind] = float(gc.text.replace('%', ''))/100

    return prob_precip

# Last water

query_watering = """
SELECT
TIMESTAMPDIFF(hour,ts,NOW()),
watered
FROM watering_log
WHERE watered in('1', 'True')
ORDER BY ts ASC
"""

def get_db_data(query, host, port, user, passwd, db):
    con = mariadb.connect(host=host, port=port, user=user, password=passwd, database=db)
    cur = con.cursor()
    cur.execute(query)

    for row in cur:
        output = row[0]

    return output



def watered_recently(hours_since_last_water, min_hours_between_watering):
    if hours_since_last_water < min_hours_between_watering:
        return True
    else:
        return False



# Determine whether to water based on rain forecast


def rain(min_precip, prob_precip, min_precip_threshold, min_precip_prob_threshold, index_max, forecast_current):
    
    output_tally = 0
        
    if forecast_current == True:
        for ind in range(0, index_max):
            if prob_precip[ind] > min_precip_prob_threshold and min_precip[ind] > min_precip_threshold:
                output_tally += 1
        if output_tally > 0:
            return True
        else:
            return False
        
# check average moisture

query_moisture = """
SELECT
avg(reading)
FROM soil_moisture
WHERE ts > DATE_SUB(now(), INTERVAL 12 HOUR)
"""


def moisture(av_moisture_L12H, min_moisture_threshold):
    if av_moisture_L12H > min_moisture_threshold:
        return True
    else:
        return False


def collate_rules(moisture_override, rain_override, watered_recently_override):
    func_list = [moisture_override, rain_override,watered_recently_override]
    if True in func_list:
        return True
    else:
        return False


# Add record to database


def insert_results(query, db_host, db_host_port, db_user, db_pass, db):

    con = mariadb.connect(host=db_host, port=db_host_port,
                       user=db_user, password=db_pass, database=db)
    cur = con.cursor()
    try:
        cur.execute(insert_stmt)
        con.commit()
    except:
        con.rollback()
    con.close()
    return


while True:
    # Get data
    get_forecast()
    tree = parse_xml(forecast_id)

    # check data
    forecast_current = check_forecast_current(tree)

    # Extract precipitation info
    min_precip = get_min_precip(index_max, tree)
    prob_precip = get_prob_precip(index_max, tree)

    min_precip_0 = min_precip[0]
    min_precip_1 = min_precip[1]
    prob_precip_0 = prob_precip[0]
    prob_precip_1 = prob_precip[1]

    # Calc time since last water
    hours_since_last_water = get_db_data(query_watering, db_host, db_host_port, db_user, db_pass, db)

    # Calc average moisture L12H
    av_moisture_L12H = get_db_data(query_moisture, db_host, db_host_port, db_user, db_pass, db)

    ## Override rules
    # Watered recently
    watered_recently_override = watered_recently(hours_since_last_water, min_hours_between_watering)

    # high soil moisture
    moisture_override = moisture(av_moisture_L12H, min_moisture_threshold)

    # rain expected
    rain_override = rain(get_min_precip(index_max, tree), get_prob_precip(index_max, tree), min_precip_threshold, min_precip_prob_threshold, index_max, forecast_current)

    # collate rules
    hold_watering = collate_rules(moisture_override, rain_override, watered_recently_override)


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
    hold_watering,
    ip_address)
    VALUES
    ({},{},{},{},{},{},{},{},{},{},{},{},{},{},{},'{}')""".format(
        forecast_current,
        min_precip_0,
        prob_precip_0,
        min_precip_1,
        prob_precip_1,
        min_precip_threshold,
        min_precip_prob_threshold,
        hours_since_last_water,
        min_hours_between_watering,
        av_moisture_L12H,
        min_moisture_threshold,
        rain_override,
        watered_recently_override,
        moisture_override,
        hold_watering,
        read_device_address()
    )

    insert_results(insert_stmt, db_host, db_host_port, db_user, db_pass, db)

    time.sleep(10800)



