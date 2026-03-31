import os
import time
from pathlib import Path

import pymysql


MYSQL_HOST = os.getenv("MYSQL_HOST", "mysql")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_ROOT_USER = os.getenv("MYSQL_ROOT_USER", "root")
MYSQL_ROOT_PASSWORD = os.getenv("MYSQL_ROOT_PASSWORD", "123qweASD")
APP_DATABASE = os.getenv("APP_DATABASE", "dip_demo")
APP_USER = os.getenv("APP_USER", "dip_user")
APP_PASSWORD = os.getenv("APP_PASSWORD", "dip_password")
MAX_RETRIES = int(os.getenv("DB_INIT_MAX_RETRIES", "30"))
RETRY_INTERVAL = int(os.getenv("DB_INIT_RETRY_INTERVAL", "2"))
SQL_PATH = Path(os.getenv("DB_INIT_SQL_PATH", "/app/init.sql"))


def connect() -> pymysql.connections.Connection:
    return pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_ROOT_USER,
        password=MYSQL_ROOT_PASSWORD,
        autocommit=True,
        charset="utf8mb4",
    )


def wait_for_mysql() -> pymysql.connections.Connection:
    last_error: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            connection = connect()
            print(f"MySQL is ready on attempt {attempt}")
            return connection
        except Exception as exc:  # pragma: no cover - bootstrap retry logging
            last_error = exc
            print(f"Waiting for MySQL ({attempt}/{MAX_RETRIES}): {exc}")
            time.sleep(RETRY_INTERVAL)

    raise RuntimeError(f"MySQL did not become ready: {last_error}")


def load_sql_script() -> str:
    sql_template = SQL_PATH.read_text(encoding="utf-8")
    return (
        sql_template.replace("{{APP_DATABASE}}", APP_DATABASE)
        .replace("{{APP_USER}}", APP_USER)
        .replace("{{APP_PASSWORD}}", APP_PASSWORD)
    )


def initialize_database(connection: pymysql.connections.Connection) -> None:
    sql_script = load_sql_script()
    statements = [
        statement.strip()
        for statement in sql_script.split(";")
        if statement.strip()
    ]

    with connection.cursor() as cursor:
        for statement in statements:
            cursor.execute(statement)


def main() -> None:
    connection = wait_for_mysql()
    try:
        initialize_database(connection)
        print("Database initialization completed")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
