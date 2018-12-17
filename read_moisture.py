import RPi.GPIO as GPIO
import time
import mysql.connector as mariadb
GPIO.setmode(GPIO.BCM)

#file = open("SensorData.txt", "w") #stores data file in same directory as this program file

db_host = 'hda.amahi.net'
db_host_port = '3306'
db_user = 'rpi'
db_pass = 'warm_me'
db = 'soil'
Pin = 17

#Define function to measure charge time
def RC_Analog(Pin):
    counter=0
    start_time = time.time()
    #Discharge capacitor
    GPIO.setup(Pin, GPIO.OUT)
    GPIO.output(Pin, GPIO.LOW)
    time.sleep(0.1) #in seconds, suspends execution.
    GPIO.setup(Pin, GPIO.IN)
#Count loops until voltage across capacitor reads high on GPIO
    while (GPIO.input(Pin)==GPIO.LOW):
        counter=counter+1
    end_time = time.time()
    return end_time - start_time


    #Main program loop
def take_reading():
    ts = time.time()
    reading = RC_Analog(Pin) #store counts in a variable
    #counter = 0
    #time_start = 0
    #time_end = 0
    return ts, reading  #return counts using GPIO4 and time
    
while True:

    insert_stmt = """
    INSERT INTO soil_moisture
    (read_ts, reading)
    VALUES
    ({},{})""".format(take_reading()[0],take_reading()[1])

    con = mariadb.connect(host = db_host, port = db_host_port, user = db_user, password = db_pass, database = db)
    cur = con.cursor()
    try:
        cur.execute(insert_stmt)
        con.commit()
    except:
        con.rollback()
    con.close()
    time.sleep(300)

GPIO.cleanup()
