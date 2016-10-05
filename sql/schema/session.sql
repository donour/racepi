BEGIN;
CREATE TABLE sessions (
       id BLOB UNIQUE PRIMARY KEY NOT NULL,
       description TEXT
);

COMMIT;

-- needed for good realtime write performance
-- PRAGMA journal_mode=WAL;


      
