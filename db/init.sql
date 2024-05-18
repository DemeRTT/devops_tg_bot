CREATE ROLE repl_user with  REPLICATION ENCRYPTED PASSWORD 'Qq12345';
SELECT pg_create_physical_replication_slot('replication_slot');
CREATE TABLE hba ( lines text );
COPY hba FROM '/var/lib/postgresql/data/pg_hba.conf';
INSERT INTO hba (lines) VALUES ('host replication all 0.0.0.0/0 md5');
COPY hba TO '/var/lib/postgresql/data/pg_hba.conf';
SELECT pg_reload_conf();
CREATE TABLE IF NOT EXISTS emails (
	id SERIAL PRIMARY KEY,
	email VARCHAR(100) UNIQUE
);
CREATE TABLE IF NOT EXISTS phone_numbers (
        id SERIAL PRIMARY KEY,
        phone_number VARCHAR(20) UNIQUE
);
INSERT INTO emails (email) VALUES ('testemail@testing.com');
INSERT INTO emails (email) VALUES ('coolemail@yandex.com');
INSERT INTO phone_numbers (phone_number) VALUES ('88005553535');
INSERT INTO phone_numbers (phone_number) VALUES ('+7(900)6667788');
