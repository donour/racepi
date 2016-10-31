--Copyright 2016 Donour Sizemore
--
--This file is part of RacePi
--
--RacePi is free software: you can redistribute it and/or modify
--it under the terms of the GNU General Public License as published by
--the Free Software Foundation, either version 3 of the License, or
--(at your option) any later version.
--
--RacePi is distributed in the hope that it will be useful,
--but WITHOUT ANY WARRANTY; without even the implied warranty of
--MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
--GNU General Public License for more details.
--
--You should have received a copy of the GNU General Public License
--along with RacePi.  If not, see <http://www.gnu.org/licenses/>.

--============================================================================
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
);COMMIT;
--============================================================================
