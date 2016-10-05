-- gpsd data
-- timestamp should be system time for when sample was collected
BEGIN;
CREATE TABLE gps_data
(
	session_id BLOB,
	timestamp DATETIME NOT NULL,
	gps_time VARCHAR,
	lat DOUBLE,
	lon DOUBLE,
	speed DOUBLE,	
	track_deg DOUBLE,
	epx DOUBLE,
	epy DOUBLE,
	epv DOUBLE,

	FOREIGN KEY(session_id) REFERENCES session(id)
);

COMMIT;
