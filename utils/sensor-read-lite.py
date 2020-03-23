import RPi.GPIO as GPIO
import time
import subprocess

GPIO.setmode(GPIO.BCM)

Pin = 17

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

    GPIO.setmode(GPIO.BCM)

    Pin = 17

    reading = RC_Analog(Pin)

    print(reading)

    time.sleep(20) #600 for prod

    GPIO.cleanup()