import xml.etree.ElementTree as ET
from ftplib import FTP
import numpy as np
from ast import literal_eval
import datetime


class weather_forecast():
    def __init__(self):

        self.index_max = 2  # number of forecast days to look ahead. 1 = rest of day, 2 = tomorrow, so on
        self.forecast_id = "IDV10450.xml"
        self.location = "VIC_PT042"


    # Get BOM forecast xml

        self.BomFtpHost = "ftp2.bom.gov.au"
        self.BomFtpPort = 21
        self.BomFtpForecastPath = "/anon/gen/fwo/"
        self.retrieve_string = 'RETR ' + self.forecast_id



    def convert_date(self, string):
        f = '%Y-%m-%dT%H:%M:%SZ'
        return datetime.datetime.strptime(string, f)


    def create_list(self):
        listofzeros = [0.0] * self.index_max
        return listofzeros


# Get forecast XML

    def get_forecast(self):
        ftp = FTP(self.BomFtpHost)
        ftp.login(user='anonymous', passwd='guest')
        ftp.cwd(self.BomFtpForecastPath)
        #ftp.retrlines('LIST')
        ftp.retrbinary(self.retrieve_string, open(self.forecast_id, 'wb').write)
        ftp.quit()
        self.tree = ET.parse(self.forecast_id)
        return

# Check whether forecast message is valid

    def check_forecast_current(self):

        issue_time = self.convert_date(self.tree.findtext("amoc/issue-time-utc"))
        expiry_time = self.convert_date(self.tree.findtext("amoc/expiry-time"))

        forecast_current = (issue_time <= datetime.datetime.utcnow() <= expiry_time)
        return forecast_current

# Extract precipitation details

# minimum forecast precipitation

    def get_min_precip(self):
        min_precip = self.create_list()
        root = self.tree.getroot()

        for loc in root.iter("area"):
            if loc.attrib['aac'] == self.location:
                for child in loc:
                    for ind in range(0, self.index_max):
                        if child.attrib['index'] == str(ind):
                            for gc in child:
                                if(gc.attrib['type'] == 'precipitation_range'):
                                    try:
                                        min_precip[ind] = np.mean([float(gc.text.split(' ')[0]), float(gc.text.split(' ')[2])])
                                    except:
                                        min_precip[ind] = float(gc.text.split(' ')[0])


        return min_precip

# probability of precipitation 

    def get_prob_precip(self):
        prob_precip = self.create_list()

        root = self.tree.getroot()

        for loc in root.iter("area"):
            if loc.attrib['aac'] == self.location:
                for child in loc:
                    for ind in range(0, self.index_max):
                        if child.attrib['index'] == str(ind):
                            for gc in child:
                                if(gc.attrib['type'] == 'probability_of_precipitation'):
                                    prob_precip[ind] = float(gc.text.replace('%', ''))/100

        return prob_precip
