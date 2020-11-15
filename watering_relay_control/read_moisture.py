from DFRobot.DFRobot_ADS1115 import ADS1115
import time
import mysql.connector as mariadb
import subprocess
from db_helper import db_helper

db_helper = db_helper()

wifi_interface = "wlan0"

ADS1115_REG_CONFIG_PGA_6_144V        = 0x00 # 6.144V range = Gain 2/3
ADS1115_REG_CONFIG_PGA_4_096V        = 0x02 # 4.096V range = Gain 1
ADS1115_REG_CONFIG_PGA_2_048V        = 0x04 # 2.048V range = Gain 2 (default)
ADS1115_REG_CONFIG_PGA_1_024V        = 0x06 # 1.024V range = Gain 4
ADS1115_REG_CONFIG_PGA_0_512V        = 0x08 # 0.512V range = Gain 8
ADS1115_REG_CONFIG_PGA_0_256V        = 0x0A # 0.256V range = Gain 16
ads1115 = ADS1115()


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

    #Main program loop

while True:

    #Set the IIC address
    ads1115.setAddr_ADS1115(0x49)
    #Sets the gain and input voltage range.
    ads1115.setGain(ADS1115_REG_CONFIG_PGA_6_144V)
    #Get the Digital Value of Analog of selected channel
    df_pipe_reading = ads1115.readVoltage(0)
    time.sleep(0.2)
    df_tape_reading = ads1115.readVoltage(1)
    time.sleep(0.2)
    vegetronix = ads1115.readVoltage(2)
    time.sleep(0.2)

    # insert_stmt = """
    # INSERT INTO soil_moisture_adc
    # (df_reading, vegetronix, ip_address)
    # VALUES
    # ({},{},'{}')""".format(df_reading.get('r'), vegetronix.get('r'), read_device_address())

    insert_stmt = """
    INSERT INTO soil_moisture_adc
    (df_pipe_reading, df_tape_reading, vegetronix, ip_address)
    VALUES
    ({},{},'{}')""".format(df_pipe_reading.get('r'), df_tape_reading.get('r'), vegetronix.get('r'), read_device_address())

    db_helper.insert_data(insert_stmt)

    time.sleep(300) #600 for prod

