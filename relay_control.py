# from Seeed Studio Wiki
# http://wiki.seeed.cc/Raspberry_Pi_Relay_Board_v1.0/

import signal
import sys
import time
import smbus
import mysql.connector as mariadb


db_host = 'hda.amahi.net'
db_host_port = '3306'
db_user = 'rpi'
db_pass = 'warm_me'
db = 'soil'


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
start_time = time.time()
relay.ON_1()
    
time.sleep(10)
relay.OFF_1()
end_time = time.time()
duration = end_time - start_time

insert_stmt = """
INSERT INTO watering
(duration)
VALUES
({})""".format(duration)

con = mariadb.connect(host = db_host, port = db_host_port, user = db_user, password = db_pass, database = db)
cur = con.cursor()
try:
    cur.execute(insert_stmt)
    con.commit()
except:
    con.rollback()
con.close()




