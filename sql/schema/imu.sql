BEGIN;
CREATE TABLE imu_data
(
	session_id BLOB NOT NULL,
	timestamp DATETIME NOT NULL,
	-- Euler Pose angles (radians)
	r DOUBLE,
	p DOUBLE,
	y DOUBLE,
	-- accel readings (g)
	x_accel DOUBLE,
	y_accel DOUBLE,	
	z_accel DOUBLE,
	-- gyro readings (radians/s)
	x_gyro DOUBLE,
	y_gyro DOUBLE,	
	z_gyro DOUBLE,
	FOREIGN KEY(session_id) REFERENCES sessions(id)
);

COMMIT;

