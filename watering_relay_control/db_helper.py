

import mysql.connector as mariadb

class db_helper():
    def __init__(self):

        self.db_host = '192.168.0.10'
        self.db_host_port = '3306'
        self.db_user = 'rpi'
        self.db_pass = 'warm_me'
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
                select min_duration,
                max_duration,
                hours_btw_watering
                from watering_params
                order by ts desc
                limit 1 
                """
        n_variables = 3
        default = 999

        return self.get_db_data(statement = statement, n_variables = n_variables, default=default)
        


    def hold_water_check(self):
        statement = """
                SELECT
                hold_watering,
                TIMESTAMPDIFF(hour,ts,NOW())
                FROM watering_rules
                order by ts desc
                limit 1
                """
        n_variables = 2
        default = 999

        return self.get_db_data(statement = statement, n_variables = n_variables, default=default)

    def get_watered(self):

        statement = """
                SELECT
                TIMESTAMPDIFF(hour, ts, NOW())
                FROM watering_log
                WHERE watered = 1
                ORDER BY ts desc
                limit 1
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




