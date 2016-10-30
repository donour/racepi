-- can bus data
-- timestamp should be system time for when sample was collected
BEGIN;
CREATE TABLE can_data
(
	session_id BLOB NOT NULL,
	timestamp DATETIME NOT NULL,
	arbitration_id integer NOT NULL, -- base (11bit) or extended (29bit)
	rtr integer NOT NULL,            -- 0 for data frames, 1 for data requests
	msg BLOB NOT NULL,               -- data payload, string of 8 hexidecimal bytes	
	FOREIGN KEY(session_id) REFERENCES sessions(id)
);

COMMIT;
