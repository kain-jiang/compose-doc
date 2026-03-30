import os
from dataclasses import dataclass


@dataclass(frozen=True)
class DatabaseSettings:
    host: str = os.getenv("MYSQL_HOST", "mysql")
    port: int = int(os.getenv("MYSQL_PORT", "3306"))
    user: str = os.getenv("MYSQL_USER", "dip_user")
    password: str = os.getenv("MYSQL_PASSWORD", "dip_password")
    database: str = os.getenv("MYSQL_DATABASE", "dip_demo")
    charset: str = os.getenv("MYSQL_CHARSET", "utf8mb4")


@dataclass(frozen=True)
class AppSettings:
    title: str = os.getenv("APP_TITLE", "dip-api")
    database: DatabaseSettings = DatabaseSettings()


settings = AppSettings()
