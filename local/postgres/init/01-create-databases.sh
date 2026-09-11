set -e

create_db() {
  local db_name="$1"
  local db_user="$2"
  local db_password="$3"

  echo "Creating database $db_name for user $db_user"

  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-SQL
    CREATE USER $db_user WITH PASSWORD '$db_password';
    CREATE DATABASE $db_name OWNER $db_user;
    REVOKE CONNECT ON DATABASE $db_name FROM PUBLIC;       -- This means only owner and the super admin can access this database.
SQL
}

create_db "user_db"         "user_service"         "$USER_DB_PASSWORD"
create_db "product_db"      "product_service"      "$PRODUCT_DB_PASSWORD"
create_db "order_db"        "order_service"        "$ORDER_DB_PASSWORD"
create_db "notification_db" "notification_service" "$NOTIFICATION_DB_PASSWORD"
create_db "suggestion_db"   "suggestion_service"   "$SUGGESTION_DB_PASSWORD"
