import logging.config
import yaml

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import httpx

from settings import settings


with open('logging.yaml', "r") as f:
    LOGGING = yaml.safe_load(f)
LOGGING["loggers"][""]["handlers"] = ["console_json", "file_json"]

logging.config.dictConfig(LOGGING)

logger = logging.getLogger(__name__)


app = FastAPI(title="API Gateway")


# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.all_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Rate Limiting Configuration using Redis
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=settings.REDIS_URL or f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)


# Service Mapping
SERVICE_MAP = {
    "users": ("users_service", 8000),
    "products": ("products_service", 8001),
    "orders": ("orders_service", 8002),
}


@app.get("/health")
@limiter.limit("100/minute")  # Health check with lenient rate limit
async def health_check(request: Request):
    return {"status": "healthy", "services": list(SERVICE_MAP.keys())}


@app.api_route("/{service}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
@limiter.limit("100/minute")  # Global rate limit per IP
async def proxy_request(
    request: Request,
    service: str,
    path: str,
):
    if service not in SERVICE_MAP:
        raise HTTPException(status_code=404, detail=f"Service '{service}' not found")

    host, port = SERVICE_MAP[service]
    backend_url = f"http://{host}:{port}/{path}"

    # Preserve query params
    query_string = request.url.query

    # Copy headers, excluding hop-by-hop headers
    headers = {}
    for key, value in request.headers.items():
        if key.lower() not in ["connection", "keep-alive", "proxy-authenticate", "proxy-authorization", "te", "trailers", "transfer-encoding", "upgrade"]:
            headers[key] = value

    original_host = request.headers.get("host")
    if original_host:
        headers["host"] = original_host

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
            # Build request kwargs
            kwargs = {
                "method": request.method,
                "url": backend_url,
                "headers": headers,
                "params": dict(request.query_params) if query_string else None,
            }

            # Handle body for methods that have it
            kwargs["content"] = await request.body()

            # Forward the request
            resp = await client.request(**kwargs)

            # Prepare response
            response = Response(
                content=resp.content,
                status_code=resp.status_code,
            )

            # Forward all response headers, including multiple Set-Cookie
            for name, value in resp.headers.multi_items():
                # Exclude hop-by-hop and content-length to prevent duplicates (FastAPI sets its own)
                if name.lower() in ["connection", "keep-alive", "proxy-authenticate", "proxy-authorization", "te", "trailers", "transfer-encoding", "upgrade", "content-length"]:
                    continue
                response.headers.append(name, value)

            return response

    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail=f"Service '{service}' is unavailable")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Proxy error: {str(e)}")