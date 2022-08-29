CREATE TABLE public.settings ( name text, value text );

INSERT INTO settings (name, value) VALUES ('c_n_boundary', '8.0');

INSERT INTO settings (name, value) VALUES ('eb_no_boundary', '6.0');

INSERT INTO settings (name, value) VALUES ('alarm_low', 'blank');

INSERT INTO settings (name, value) VALUES ('alarm_normal', 'green');

INSERT INTO settings (name, value) VALUES ('alarm_medium', 'gray');

INSERT INTO settings (name, value) VALUES ('alarm_high', 'yellow');

INSERT INTO settings (name, value) VALUES ('alarm_critical', 'red');

CREATE TABLE public.users ( login text, password text );

INSERT INTO users (login, password) VALUES ('admin', 'admin');

INSERT INTO users (login, password) VALUES ('monitor', 'monitor');
