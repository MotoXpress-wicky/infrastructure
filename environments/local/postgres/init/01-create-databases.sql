-- Creates one database and one DB user per service.
-- The Postgres container runs this file with psql, only when its data volume is empty.
-- To run it again: docker compose down -v   (WARNING: deletes all databases)
--
-- \getenv reads a password from the container's environment (env/postgres.env) into a psql
-- variable. :'name' then inserts it as a safely quoted SQL string.
-- If a password is missing, the statement fails and the container stops with an error.

\getenv user_db_password USER_DB_PASSWORD
\getenv product_db_password PRODUCT_DB_PASSWORD
\getenv order_db_password ORDER_DB_PASSWORD
\getenv notification_db_password NOTIFICATION_DB_PASSWORD
\getenv payment_db_password PAYMENT_DB_PASSWORD

-- REVOKE ... FROM PUBLIC: only the owner (and the admin user) may connect to each database.

CREATE USER user_service WITH PASSWORD :'user_db_password';
CREATE DATABASE user_db OWNER user_service;
REVOKE CONNECT ON DATABASE user_db FROM PUBLIC;

CREATE USER product_service WITH PASSWORD :'product_db_password';
CREATE DATABASE product_db OWNER product_service;
REVOKE CONNECT ON DATABASE product_db FROM PUBLIC;

CREATE USER order_service WITH PASSWORD :'order_db_password';
CREATE DATABASE order_db OWNER order_service;
REVOKE CONNECT ON DATABASE order_db FROM PUBLIC;

CREATE USER notification_service WITH PASSWORD :'notification_db_password';
CREATE DATABASE notification_db OWNER notification_service;
REVOKE CONNECT ON DATABASE notification_db FROM PUBLIC;

CREATE USER payment_service WITH PASSWORD :'payment_db_password';
CREATE DATABASE payment_db OWNER payment_service;
REVOKE CONNECT ON DATABASE payment_db FROM PUBLIC;
