--Copyright 2017 Donour Sizemore
--
--This file is part of RacePi
--
--RacePi is free software: you can redistribute it and/or modify
--it under the terms of the GNU General Public License as published by
--the Free Software Foundation, version 2.
--
--RacePi is distributed in the hope that it will be useful,
--but WITHOUT ANY WARRANTY; without even the implied warranty of
--MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
--GNU General Public License for more details.
--
--You should have received a copy of the GNU General Public License
--along with RacePi.  If not, see <http://www.gnu.org/licenses/>.

--============================================================================
-- Tire data
-- timestamp should be system time for when sample was collected
BEGIN;
CREATE TABLE tire_data
(
	session_id BLOB NOT NULL,
	timestamp DATETIME NOT NULL,
	lf_pressure DOUBLE,
	rf_pressure DOUBLE,	
	lr_pressure DOUBLE,
	rr_pressure DOUBLE,
	lf_temp DOUBLE,
	rf_temp DOUBLE,	
	lr_temp DOUBLE,
	rr_temp DOUBLE,

	-- battery status
	lf_sensor_battery integer,
	rf_sensor_battery integer,	
	lr_sensor_battery integer,
	rr_sensor_battery integer,


	FOREIGN KEY(session_id) REFERENCES sessions(id)
);COMMIT;
--============================================================================
