import asyncio
from urllib.parse import urljoin, urlparse
import httpx

from fastapi import APIRouter, Request, Response, WebSocket, WebSocketDisconnect, HTTPException, Depends

from backend.database import get_db
from backend.models import ProxyService
from starlette.types import Receive, Scope, Send

proxy_router = APIRouter(prefix="/api/proxy", tags=["proxy"])

INJECTED_JS = '<script src="/static/injection.js"></script>'

def adjust_set_cookie_header(set_cookie_value: str, proxy_path_prefix: str) -> str:
    """
    Modify the 'Path' attribute in Set-Cookie header to use proxy path,
    so that cookies are correctly scoped in browser.
    """
    parts = set_cookie_value.split(";")
    new_parts = []
    found_path = False
    for part in parts:
        if part.strip().lower().startswith("path="):
            found_path = True
            new_parts.append(f"Path={proxy_path_prefix}")
        else:
            new_parts.append(part)
    if not found_path:
        new_parts.append(f"Path={proxy_path_prefix}")
    return ";".join(new_parts)

async def inject_javascript(content: bytes) -> bytes:
    """
    Inject JS snippet in HTML content.
    """
    closing_body_tag = b"</body>"
    idx = content.lower().find(closing_body_tag)
    if idx == -1:
        return content
    return content[:idx] + INJECTED_JS.encode("utf-8") + content[idx:]

@proxy_router.api_route(
    "/{service_name}/{full_path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
)
@proxy_router.api_route("/{service_name}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def proxy_http(
    service_name: str,
    full_path: str = "",
    request: Request = None,
    db=Depends(get_db),
):
    service = db.query(ProxyService).filter_by(name=service_name, enabled=True).first()
    if not service:
        raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found or disabled")

    # Compose target URL
    target_url = urljoin(service.base_url.rstrip("/") + "/", full_path.lstrip("/"))

    # Forward headers except Host
    headers = {k: v for k, v in request.headers.items() if k.lower() != "host"}

    async with httpx.AsyncClient(timeout=None, follow_redirects=False) as client:
        try:
            body = await request.body()
            resp = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body,
                cookies=request.cookies,
                params=request.query_params,
            )
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Upstream unreachable: {str(e)}")

    excluded_headers = {
        "content-encoding",
        "content-length",
        "transfer-encoding",
        "connection",
        "content-security-policy",
    }

    response_headers = []
    proxy_prefix = f"/api/proxy/{service_name}"

    # Adjust Location header for redirects
    location = resp.headers.get("Location")
    for k, v in resp.headers.items():
        if k.lower() in excluded_headers:
            continue
        if k.lower() == "location" and location and location.startswith("/"):
            new_location = proxy_prefix + location
            response_headers.append(("Location", new_location))
        # Adjust Set-Cookie header path attribute for proxy
        elif k.lower() == "set-cookie":
            new_cookie = adjust_set_cookie_header(v, proxy_prefix)
            response_headers.append((k, new_cookie))
        else:
            response_headers.append((k, v))

    content = resp.content
    content_type = resp.headers.get("content-type", "").lower()
    if "text/html" in content_type:
        content = await inject_javascript(content)

    return Response(content=content, status_code=resp.status_code, headers=dict(response_headers))


@proxy_router.websocket("/{service_name}/{full_path:path}")
async def proxy_websocket(
    websocket: WebSocket,
    service_name: str,
    full_path: str,
    db=Depends(get_db),
):
    await websocket.accept()

    service = db.query(ProxyService).filter_by(name=service_name, enabled=True).first()
    if not service:
        await websocket.close(code=1008)  # Policy Violation
        return

    # Prepare WebSocket URL (convert http(s) to ws(s))
    base_url = service.base_url
    if base_url.startswith("https://"):
        ws_url = "wss://" + base_url[len("https://") :]
    elif base_url.startswith("http://"):
        ws_url = "ws://" + base_url[len("http://") :]
    else:
        ws_url = base_url

    target_ws_url = urljoin(ws_url.rstrip("/") + "/", full_path.lstrip("/"))

    async with httpx.AsyncClient() as client:
        try:
            async with client.ws_connect(target_ws_url) as upstream_ws:

                async def forward_upstream_to_client():
                    async for message in upstream_ws.iter_bytes():
                        await websocket.send_bytes(message)

                async def forward_client_to_upstream():
                    try:
                        while True:
                            message = await websocket.receive_bytes()
                            await upstream_ws.send_bytes(message)
                    except WebSocketDisconnect:
                        pass

                await asyncio.gather(forward_upstream_to_client(), forward_client_to_upstream())

        except Exception:
            await websocket.close(code=1011)  # Internal error