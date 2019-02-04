import RPi.GPIO as GPIO
import time
import mysql.connector as mariadb
import subprocess

GPIO.setmode(GPIO.BCM)

#file = open("SensorData.txt", "w") #stores data file in same directory as this program file

wifi_interface = "wlan0"
db_host = 'hda.amahi.net'
db_host_port = '3306'
db_user = 'rpi'
db_pass = 'warm_me'
db = 'soil'
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
def take_reading():
    reading_time = RC_Analog(Pin)[1] #store counts in a variable
    reading_count = RC_Analog(Pin)[0]
    #counter = 0
    #time_start = 0
    #time_end = 0
    return reading_time, reading_count  #return counts using GPIO4 and time
    
while True:

    insert_stmt = """
    INSERT INTO soil_moisture
    (reading, reading_count, ip_address)
    VALUES
    ({},{},'{}')""".format(take_reading()[0], take_reading()[1], read_device_address())

    con = mariadb.connect(host = db_host, port = db_host_port, user = db_user, password = db_pass, database = db)
    cur = con.cursor()
    try:
        cur.execute(insert_stmt)
        con.commit()
    except:
        con.rollback()
    con.close()
    time.sleep(600)

GPIO.cleanup()
