import os
import time

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


def initialize_database(connection: pymysql.connections.Connection) -> None:
    with connection.cursor() as cursor:
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{APP_DATABASE}`")
        cursor.execute(
            f"CREATE USER IF NOT EXISTS '{APP_USER}'@'%' IDENTIFIED BY '{APP_PASSWORD}'"
        )
        cursor.execute(
            f"ALTER USER '{APP_USER}'@'%' IDENTIFIED BY '{APP_PASSWORD}'"
        )
        cursor.execute(
            f"GRANT ALL PRIVILEGES ON `{APP_DATABASE}`.* TO '{APP_USER}'@'%'"
        )
        cursor.execute("FLUSH PRIVILEGES")
        cursor.execute(f"USE `{APP_DATABASE}`")
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS demo_messages (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(128) NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute("SELECT COUNT(*) FROM demo_messages")
        row_count = cursor.fetchone()[0]
        if row_count == 0:
            cursor.executemany(
                """
                INSERT INTO demo_messages (title, content)
                VALUES (%s, %s)
                """,
                [
                    ("welcome", "dip-db-init inserted the first demo record"),
                    ("status", "dip-api can now read MySQL data through /api/dip-api/messages"),
                ],
            )


def main() -> None:
    connection = wait_for_mysql()
    try:
        initialize_database(connection)
        print("Database initialization completed")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
