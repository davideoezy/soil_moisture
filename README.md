soil_moisture

Setup

Create 3 DB tables - soil_moisture, watering_rules & watering_log

Setup nodes (may all be on 1)

1. device reading moisture:
sudo apt-get install python-rpi.gpio python3-rpi.gpio
cp soil_reader.service /etc/systemd/system/
sudo systemctl enable soil_reader.service

2. device running rules:
cp watering_rules.service /etc/systemd/system
sudo systemctl  enable watering_rules.service

3.  device switching on water:
crontab schedule watering_trigger.py once a day



