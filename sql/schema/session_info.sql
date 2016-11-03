--Copyright 2016 Donour Sizemore
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
-- session_info data
-- timestamp should be system time for when sample was collected
-- this data is not collected from sensors, but generated in post processing
-- each entry should correspond to a distinct session
BEGIN;
CREATE TABLE session_info
(
	session_id BLOB UNIQUE PRIMARY KEY NOT NULL,
	start_time_utc DATETIME NOT NULL,
	duration DOUBLE,
	max_speed DOUBLE,
	num_data_samples INTEGER,
	FOREIGN KEY(session_id) REFERENCES sessions(id)
);COMMIT;
--============================================================================