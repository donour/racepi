BEGIN;
CREATE TABLE imu_data
(
	session_id BLOB NOT NULL,
	timestamp DATETIME NOT NULL,
	r DOUBLE,
	p DOUBLE,
	y DOUBLE,
	x_accel DOUBLE,
	y_accel DOUBLE,	
	z_accel DOUBLE,
	x_gyro DOUBLE,
	y_gyro DOUBLE,	
	z_gyro DOUBLE,
	FOREIGN KEY(session_id) REFERENCES sessions(id)
);

COMMIT;

