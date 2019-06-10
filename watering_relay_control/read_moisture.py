import RPi.GPIO as GPIO
import time
import mysql.connector as mariadb
import subprocess
from db_helper import db_helper

db_helper = db_helper()

GPIO.setmode(GPIO.BCM)

wifi_interface = "wlan0"
Pin = 17


def read_device_address():
    try:
        proc = subprocess.Popen(
            ["ifconfig", wifi_interface], stdout=subprocess.PIPE, universal_newlines=True)
        out, err = proc.communicate()
        IP = ""
        for line in out.split("\n"):
            if("192.168" in line):
                strings = line.split(" ")
                device_address = strings[9]
                return(device_address)
    except:
        return("ERROR!-ifconfig")

#Define function to measure charge time
def RC_Analog(Pin):
    fudgeFactor = 100
    sleepTime = 0.1 # in seconds
    counter=0
    start_time = time.time()
    #Discharge capacitor
    GPIO.setup(Pin, GPIO.OUT)
    GPIO.output(Pin, GPIO.LOW)
    time.sleep(sleepTime) #in seconds, suspends execution.
    GPIO.setup(Pin, GPIO.IN)
#Count loops until voltage across capacitor reads high on GPIO
    while (GPIO.input(Pin)==GPIO.LOW):
        counter=counter+1
    end_time = time.time()
    return counter, ((end_time - start_time)-sleepTime)*fudgeFactor


    #Main program loop

while True:

    reading = RC_Analog(Pin)

    insert_stmt = """
    INSERT INTO soil_moisture
    (reading, reading_count, ip_address)
    VALUES
    ({},{},'{}')""".format(reading[0], reading[1], read_device_address())

    db_helper.insert_data(insert_stmt)

    time.sleep(600) #600 for prod

    GPIO.cleanup()
