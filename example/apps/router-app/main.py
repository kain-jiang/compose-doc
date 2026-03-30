from fastapi import FastAPI, Request


app = FastAPI(title="router-app")


@app.get("/")
def read_root() -> dict[str, object]:
    return {
        "app": "router-app",
        "message": "FastAPI catch-all demo service",
        "routes": [
            "/",
            "/healthz",
            "/{path:path}",
        ],
    }


@app.get("/healthz")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.api_route(
    "/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
)
async def catch_all(path: str, request: Request) -> dict[str, object]:
    body = await request.body()
    return {
        "app": "router-app",
        "path": path,
        "method": request.method,
        "query": dict(request.query_params),
        "headers": {
            key: value
            for key, value in request.headers.items()
            if key in {"host", "user-agent", "content-type"}
        },
        "body": body.decode("utf-8", errors="replace"),
    }
