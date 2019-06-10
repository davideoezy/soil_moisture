
from db_helper import db_helper

db_helper = db_helper()

class rules():
    def __init__(self):
        self.min_precip_threshold = db_helper.get_parameters()[0]  # mm expected
        self.min_precip_prob_threshold = db_helper.get_parameters()[1]  # % chance of rain
        self.min_hours_between_watering = db_helper.get_parameters()[2]
        self.min_moisture_threshold = db_helper.get_parameters()[3]  # taken from moisture readings. Average over 12 hours
        self.index_max = 2


    def watered_recently(self, hours_since_last_water):
        if hours_since_last_water < self.min_hours_between_watering:
            return True
        else:
            return False



# Determine whether to water based on rain forecast


    def rain(self, min_precip, prob_precip, forecast_current):
        
        output_tally = 0
            
        if forecast_current == True:
            for ind in range(0, self.index_max):
                if prob_precip[ind] > self.min_precip_prob_threshold and min_precip[ind] > self.min_precip_threshold:
                    output_tally += 1
            if output_tally > 0:
                return True
            else:
                return False


    def moisture(self, av_moisture_L12H):
        if av_moisture_L12H > self.min_moisture_threshold:
            return True
        else:
            return False


    def collate_rules(self, moisture_override, rain_override, watered_recently_override):
        func_list = [moisture_override, rain_override,watered_recently_override]
        if True in func_list:
            return True
        else:
            return False