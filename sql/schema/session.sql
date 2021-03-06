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
-- session data
BEGIN;
CREATE TABLE sessions (
       id BLOB UNIQUE PRIMARY KEY NOT NULL,
       description TEXT
);COMMIT;
--============================================================================

-- This _may_ be needed for good realtime write performance
-- PRAGMA journal_mode=WAL;


      
