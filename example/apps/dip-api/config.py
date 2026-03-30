from dataclasses import dataclass
from pathlib import Path

import yaml


CONFIG_PATH = Path(__file__).with_name("config.yaml")


@dataclass(frozen=True)
class DatabaseSettings:
    host: str
    port: int
    user: str
    password: str
    database: str
    charset: str


@dataclass(frozen=True)
class AppSettings:
    title: str
    database: DatabaseSettings


def load_settings() -> AppSettings:
    with CONFIG_PATH.open("r", encoding="utf-8") as config_file:
        data = yaml.safe_load(config_file) or {}

    database = data.get("database", {})
    return AppSettings(
        title=data.get("title", "dip-api"),
        database=DatabaseSettings(
            host=database.get("host", "mysql"),
            port=int(database.get("port", 3306)),
            user=database.get("user", "dip_user"),
            password=database.get("password", "dip_password"),
            database=database.get("database", "dip_demo"),
            charset=database.get("charset", "utf8mb4"),
        ),
    )


settings = load_settings()
