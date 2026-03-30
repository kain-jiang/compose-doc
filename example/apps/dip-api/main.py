import pymysql
from fastapi import FastAPI, Request
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


@app.get("/")
def read_root() -> dict[str, object]:
    return {
        "app": settings.title,
        "message": "FastAPI catch-all demo service for DIP",
        "routes": [
            "/",
            "/healthz",
            "/api/dip-api/{path:path}",
        ],
    }


@app.get("/healthz")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


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
