

import mysql.connector as mariadb

class db_helper():
    def __init__(self):

        self.db_host = '192.168.0.10'
        self.db_host_port = '3316'
        self.db_user = 'rpi'
        self.db_pass = 'water_me'
        self.db = 'soil'


    def get_db_data(self, n_variables, statement, default):

        con = mariadb.connect(host=self.db_host, port=self.db_host_port, user=self.db_user,
                              password=self.db_pass, database=self.db)
        cur = con.cursor()

        cur.execute(statement)

        if n_variables == 1:
            output = default

            for row in cur:
                output = row[0]
            
            return output

        elif n_variables > 1:
            output = [default] * n_variables

            for row in cur:
                output = row

            return output



    def get_parameters(self):
        statement = """
                select min_precip_threshold,
                min_precip_prob_threshold,
                min_hours_between_watering,
                min_moisture_threshold
                from watering_params
                order by ts desc
                limit 1 
                """
        n_variables = 4
        default = 999

        return self.get_db_data(statement = statement, n_variables = n_variables, default=default)
        


    def get_last_water(self):
        statement = """
                SELECT
                TIMESTAMPDIFF(hour,ts,NOW()),
                watered
                FROM watering_log
                WHERE watered = 1
                ORDER BY ts ASC
                """
        n_variables = 1
        default = 999

        return self.get_db_data(statement = statement, n_variables = n_variables, default=default)

    def get_av_water(self):

        statement = """
                SELECT
                avg(vegetronix)
                FROM soil_moisture_adc
                WHERE ts > DATE_SUB(now(), INTERVAL 1 HOUR)
                """
        n_variables = 1
        default = 999
        return self.get_db_data(statement = statement, n_variables = n_variables, default=default)
    

    def insert_data(self, query):

        con = mariadb.connect(host=self.db_host, port=self.db_host_port,
                        user=self.db_user, password=self.db_pass, database=self.db)
        cur = con.cursor()
        try:
            cur.execute(query)
            con.commit()
        except:
            con.rollback()
        con.close()
        return




