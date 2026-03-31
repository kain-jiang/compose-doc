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
class RedisSettings:
    host: str
    port: int
    db: int


@dataclass(frozen=True)
class KafkaSettings:
    bootstrap_servers: str
    topic: str


@dataclass(frozen=True)
class OpenSearchSettings:
    hosts: list[str]
    use_ssl: bool
    verify_certs: bool


@dataclass(frozen=True)
class AppSettings:
    title: str
    database: DatabaseSettings
    redis: RedisSettings
    kafka: KafkaSettings
    opensearch: OpenSearchSettings


def load_settings() -> AppSettings:
    with CONFIG_PATH.open("r", encoding="utf-8") as config_file:
        data = yaml.safe_load(config_file) or {}

    database = data.get("database", {})
    redis = data.get("redis", {})
    kafka = data.get("kafka", {})
    opensearch = data.get("opensearch", {})

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
        redis=RedisSettings(
            host=redis.get("host", "redis"),
            port=int(redis.get("port", 6379)),
            db=int(redis.get("db", 0)),
        ),
        kafka=KafkaSettings(
            bootstrap_servers=kafka.get("bootstrap_servers", "kafka:9092"),
            topic=kafka.get("topic", "dip-demo"),
        ),
        opensearch=OpenSearchSettings(
            hosts=list(opensearch.get("hosts", ["http://opensearch:9200"])),
            use_ssl=bool(opensearch.get("use_ssl", False)),
            verify_certs=bool(opensearch.get("verify_certs", False)),
        ),
    )


settings = load_settings()
