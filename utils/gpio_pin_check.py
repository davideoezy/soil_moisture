import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)

output = []

for Pin in range(0,20):
    GPIO.setup(Pin, GPIO.OUT)
    GPIO.output(Pin, GPIO.LOW)
    GPIO.setup(Pin, GPIO.IN)
    out = Pin, GPIO.input(Pin)
    output.append(out)

print(output)