-- gpsd data
-- timestamp should be system time for when sample was collected
BEGIN;
CREATE TABLE gps_data
(
	session_id BLOB NOT NULL,
	timestamp DATETIME NOT NULL,
	time VARCHAR,
	lat DOUBLE,
	lon DOUBLE,
	speed DOUBLE,	
	track DOUBLE,
	epx DOUBLE,
	epy DOUBLE,
	epv DOUBLE,

	FOREIGN KEY(session_id) REFERENCES sessions(id)
);

COMMIT;
