
import signal
import sys
import time
import smbus
from ast import literal_eval


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

relay.ON_1()
time.sleep(10)
relay.OFF_1()
