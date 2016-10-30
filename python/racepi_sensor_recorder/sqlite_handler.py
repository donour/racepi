import uuid
import sqlite3


class DbHandler:
    """
    Class for handling RacePi access to sqlite
    """
    def __init__(self, db_location):
        
        self.conn = sqlite3.connect(db_location)
        if self.conn is None:
            raise IOError("Could not open db: " + db_location)
        self.conn.execute("PRAGMA foreign_keys = ON;");
        self.conn.execute("PRAGMA journal_mode=WAL;")
        
        
    def get_new_session(self):
        """
        Create new session entry in DB and return the 
        session ID.
        """
        session_id = uuid.uuid1()
        insert_cmd = """
        insert into sessions (id, description)
        values ('%s', 'Created by RacePi')
        """ % session_id.hex
        self.conn.execute(insert_cmd)
        return session_id

    
    def insert_imu_updates(self, imu_data, session_id):
        for sample in imu_data:
            if sample:
                t = sample[0]
                pose = sample[1]['fusionPose']
                accel= sample[1]['accel']
                gyro = sample[1]['gyro']

                #os.write(1, "\r[%.3f] %2.4f %2.4f %2.4f" % (
                #    t,pose[0], pose[1], pose[2]))

                insert_cmd = """
                  insert into imu_data
                  (session_id, timestamp,
                   r, p, y, x_accel, y_accel, z_accel, x_gyro, y_gyro, z_gyro)
                  values
                  ('%s', %s,
                   %f, %f, %f, %f, %f, %f, %f, %f, %f)
                """ % (
                    (session_id.hex, t) +
                     tuple(pose) + tuple(accel) + tuple(gyro))
                self.conn.execute(insert_cmd)

        if imu_data:
            self.conn.commit()
                

    def insert_gps_updates(self, gps_data, session_id):
        field_names = GPS_REQUIRED_FIELDS

        for sample in gps_data:
            # system time of sample
            t = sample[0]   
            # extract just the fields we use
            d = map(sample[1].get, field_names)
            available_fields = sample[1].keys()          

            # the sample is only usuable if it has velocity
            if 'speed' in available_fields:                
                insert_cmd = """
                  insert into gps_data
                  (session_id, timestamp,
                   %s)
                  values
                  ('%s', %s,
                   '%s', %f, %f, %f, %f, %f, %f, %f)
                """ % (
                    (','.join(field_names),
                    session_id.hex, t)  + tuple(d))
                self.conn.execute(insert_cmd)

        if gps_data:
            self.conn.commit()  


