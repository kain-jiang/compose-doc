import pymysql
import redis
from fastapi import FastAPI, Request
from kafka import KafkaProducer
from opensearchpy import OpenSearch
from config import settings


app = FastAPI(title=settings.title)


def get_connection() -> pymysql.connections.Connection:
    return pymysql.connect(
        host=settings.database.host,
        port=settings.database.port,
        user=settings.database.user,
        password=settings.database.password,
        database=settings.database.database,
        autocommit=True,
        cursorclass=pymysql.cursors.DictCursor,
        charset=settings.database.charset,
    )


def get_redis_client() -> redis.Redis:
    return redis.Redis(
        host=settings.redis.host,
        port=settings.redis.port,
        db=settings.redis.db,
        decode_responses=True,
    )


def get_kafka_producer() -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=settings.kafka.bootstrap_servers,
        value_serializer=lambda value: value.encode("utf-8"),
    )


def get_opensearch_client() -> OpenSearch:
    return OpenSearch(
        hosts=settings.opensearch.hosts,
        use_ssl=settings.opensearch.use_ssl,
        verify_certs=settings.opensearch.verify_certs,
    )


def verify_opensearch(opensearch_client: OpenSearch) -> dict[str, object]:
    info = opensearch_client.info()
    index_name = settings.opensearch.index
    document_id = f"{settings.title}-dependency-check"
    document = {
        "app": settings.title,
        "category": "dependency-check",
        "message": "OpenSearch write and search verification from dip-api",
    }

    if not opensearch_client.indices.exists(index=index_name):
        opensearch_client.indices.create(index=index_name)

    opensearch_client.index(
        index=index_name,
        id=document_id,
        body=document,
        refresh=True,
    )

    search_result = opensearch_client.search(
        index=index_name,
        body={
            "size": 5,
            "query": {
                "term": {
                    "category.keyword": "dependency-check",
                }
            },
        },
    )
    hits = search_result.get("hits", {}).get("hits", [])

    return {
        "status": "ok",
        "cluster_name": info.get("cluster_name"),
        "version": info.get("version", {}).get("number"),
        "index": index_name,
        "document_id": document_id,
        "hit_count": len(hits),
        "sample_document": hits[0].get("_source") if hits else document,
    }


@app.get("/")
def read_root() -> dict[str, object]:
    return {
        "app": settings.title,
        "message": "FastAPI catch-all demo service for DIP",
        "routes": [
            "/",
            "/healthz",
            "/api/dip-api/dependencies",
            "/api/dip-api/{path:path}",
        ],
    }


@app.get("/healthz")
def healthcheck() -> dict[str, object]:
    dependency_status = read_dependencies()
    overall_status = "ok" if all(
        item["status"] == "ok" for item in dependency_status["dependencies"].values()
    ) else "degraded"
    return {
        "status": overall_status,
        **dependency_status,
    }


@app.get("/api/dip-api/messages")
def read_messages() -> dict[str, object]:
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, title, content, created_at
                FROM demo_messages
                ORDER BY id ASC
                """
            )
            messages = cursor.fetchall()
    finally:
        connection.close()

    return {
        "app": settings.title,
        "database": settings.database.database,
        "count": len(messages),
        "messages": messages,
    }


@app.get("/api/dip-api/dependencies")
def read_dependencies() -> dict[str, object]:
    dependencies: dict[str, dict[str, object]] = {}

    try:
        connection = get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1 AS ok")
                cursor.fetchone()
            dependencies["mysql"] = {
                "status": "ok",
                "database": settings.database.database,
            }
        finally:
            connection.close()
    except Exception as exc:
        dependencies["mysql"] = {"status": "error", "detail": str(exc)}

    try:
        redis_client = get_redis_client()
        redis_client.ping()
        cache_key = "dip-api:demo:last-check"
        redis_client.set(cache_key, settings.title)
        dependencies["redis"] = {
            "status": "ok",
            "host": settings.redis.host,
            "port": settings.redis.port,
            "sample_key": cache_key,
            "sample_value": redis_client.get(cache_key),
        }
    except Exception as exc:
        dependencies["redis"] = {"status": "error", "detail": str(exc)}

    try:
        producer = get_kafka_producer()
        try:
            future = producer.send(
                settings.kafka.topic,
                f"{settings.title} dependency check",
            )
            metadata = future.get(timeout=10)
            dependencies["kafka"] = {
                "status": "ok",
                "bootstrap_servers": settings.kafka.bootstrap_servers,
                "topic": metadata.topic,
                "partition": metadata.partition,
                "offset": metadata.offset,
            }
        finally:
            producer.flush()
            producer.close()
    except Exception as exc:
        dependencies["kafka"] = {"status": "error", "detail": str(exc)}

    try:
        opensearch_client = get_opensearch_client()
        dependencies["opensearch"] = verify_opensearch(opensearch_client)
    except Exception as exc:
        dependencies["opensearch"] = {"status": "error", "detail": str(exc)}

    return {
        "app": settings.title,
        "dependencies": dependencies,
    }


@app.api_route(
    "/api/dip-api/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
)
async def catch_all(path: str, request: Request) -> dict[str, object]:
    body = await request.body()
    return {
        "app": settings.title,
        "path": path,
        "full_path": f"/api/dip-api/{path}",
        "method": request.method,
        "query": dict(request.query_params),
        "headers": {
            key: value
            for key, value in request.headers.items()
            if key in {"host", "user-agent", "content-type"}
        },
        "body": body.decode("utf-8", errors="replace"),
    }
