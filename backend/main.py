import os
from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from backend.auth import auth_bp
from backend.proxy import proxy_bp
from backend.crud import crud_bp

app = FastAPI(title="CentralArr API")

# Add session middleware with secret key (needed for auth session)
app.add_middleware(SessionMiddleware, secret_key=os.environ.get("SECRET_KEY", "supersecret"))

# Enable CORS for frontend dev server or front production
origins = [
    "http://localhost",
    "http://localhost:5173",  # Vue dev server default port
    # Add your frontend production URLs as needed
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth_bp, prefix="/api/auth", tags=["auth"])
app.include_router(proxy_router, prefix="/api/proxy", tags=["proxy"])
app.include_router(ws_router, prefix="/api/proxy", tags=["proxy"])
app.include_router(crud_bp, prefix="/api/crud", tags=["crud"])

# Serve Vue.js static files on prod
FASTAPI_ENV = os.environ.get("FLASK_ENV", "prod")


if FASTAPI_ENV == "prod":
    # Mount static files (assuming Vue build output in frontend/dist)
    app.mount("/", StaticFiles(directory="static", html=True), name="frontend")

else:
    # Dev mode: proxy Vue dev server for frontend requests

    from fastapi.responses import StreamingResponse
    import httpx

    VUE_DEV_SERVER = "http://localhost:5173"

    @app.get("/{full_path:path}")
    async def proxy_vue_dev_server(full_path: str, request: Request):
        """
        Proxy frontend requests to Vue dev server in dev mode
        """
        url = f"{VUE_DEV_SERVER}/{full_path}"
        headers = dict(request.headers)
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=request.method,
                url=url,
                headers=headers,
                params=request.query_params,
                content=await request.body(),
                timeout=10.0,
            )
        return Response(content=response.content, status_code=response.status_code, headers=response.headers)

# Health check endpoint
@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}