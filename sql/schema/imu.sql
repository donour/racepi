BEGIN;
CREATE TABLE imu_data
(
	id BLOB,
	timestamp DATETIME,
	r DOUBLE,
	p DOUBLE,
	y DOUBLE,
	x_accel DOUBLE,
	y_accel DOUBLE,	
	z_accel DOUBLE
);

COMMIT;

-- needed for good realtime write performance
PRAGMA journal_mode=WAL;

