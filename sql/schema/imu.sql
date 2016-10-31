--Copyright 2016 Donour Sizemore
--
--This file is part of RacePi
--
--RacePi is free software: you can redistribute it and/or modify
--it under the terms of the GNU General Public License as published by
---the Free Software Foundation, version 2.
--
--RacePi is distributed in the hope that it will be useful,
--but WITHOUT ANY WARRANTY; without even the implied warranty of
--MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
--GNU General Public License for more details.
--
--You should have received a copy of the GNU General Public License
--along with RacePi.  If not, see <http://www.gnu.org/licenses/>.

--============================================================================
-- imu sensor data
-- timestamp should be system time for when sample was collected
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
);COMMIT;
--============================================================================
