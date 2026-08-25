import base64
import hashlib
import hmac
import json
import logging
import os
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Path as PathParam, Query, Request, Response, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# Configure structured Python logger
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("streamwave")

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "media.json"
PUBLIC_DIR = BASE_DIR / "public"
MEDIA_DIR = PUBLIC_DIR / "media"
IMAGES_DIR = PUBLIC_DIR / "images"

PREVIEW_VIDEO_FILE = MEDIA_DIR / "streamwave-preview.mp4"
LOGO_IMAGE_FILE = IMAGES_DIR / "streamwave-logo.png"

# Centralized Subscription Plan Configuration
SUBSCRIPTION_PLAN = {
    "id": "streamwave-monthly",
    "name": "StreamWave Monthly",
    "price": "US$2.99 per month",
    "price_amount": 2.99,
    "currency": "USD",
    "interval": "month",
    "benefits": [
        "Full Zimbabwean catalogue access",
        "5-second MP4 movie previews",
        "Demonstration music audio samples",
        "Access on desktop or mobile",
    ],
}

# Session Cookie Signing Secret (Read from environment variable, never hardcoded in production)
DEMO_SESSION_SECRET = os.getenv(
    "DEMO_SESSION_SECRET", "streamwave-secret-key-academic-demo-2026"
).encode("utf-8")


def create_session_token(email: str, expiry_seconds: int = 86400 * 7) -> str:
    """Generates an HMAC-SHA256 signed session token for a paid demonstration member."""
    payload = {
        "email": email.strip().lower(),
        "plan_id": SUBSCRIPTION_PLAN["id"],
        "exp": int(time.time()) + expiry_seconds,
    }
    json_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    b64_payload = base64.urlsafe_b64encode(json_bytes).decode("utf-8").rstrip("=")

    signature = hmac.new(DEMO_SESSION_SECRET, b64_payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{b64_payload}.{signature}"


def verify_session_token(token: str) -> Optional[dict]:
    """Verifies and decodes an HMAC-SHA256 signed session token using constant-time digest comparison."""
    if not token or "." not in token:
        return None
    try:
        b64_payload, signature = token.rsplit(".", 1)
        expected_sig = hmac.new(DEMO_SESSION_SECRET, b64_payload.encode("utf-8"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected_sig, signature):
            return None

        padded_b64 = b64_payload + "=" * (-len(b64_payload) % 4)
        payload_bytes = base64.urlsafe_b64decode(padded_b64.encode("utf-8"))
        payload = json.loads(payload_bytes.decode("utf-8"))

        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except Exception as e:
        logger.warning(f"Session token verification error: {e}")
        return None


# --- Asset Initialization Helpers ---

def ensure_video_preview_asset():
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    if not PREVIEW_VIDEO_FILE.exists() or PREVIEW_VIDEO_FILE.stat().st_size == 0:
        downloads_dir = Path(r"C:\Users\dell\Downloads")
        candidate_sources = [
            downloads_dir / "Use_the_uploaded_StreamWave_lo.mp4",
            downloads_dir / "Download (28).mp4",
        ]
        for src in candidate_sources:
            if src.exists() and src.stat().st_size > 0:
                try:
                    shutil.copyfile(src, PREVIEW_VIDEO_FILE)
                    logger.info(f"Copied StreamWave preview MP4 video from {src} to {PREVIEW_VIDEO_FILE}")
                    break
                except Exception as e:
                    logger.error(f"Failed to copy video asset from {src}: {e}")


def ensure_logo_asset():
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    if not LOGO_IMAGE_FILE.exists() or LOGO_IMAGE_FILE.stat().st_size == 0:
        src = BASE_DIR / ".user_uploaded" / "media_1787682860034.png"
        if not src.exists():
            src = BASE_DIR / ".user_uploaded" / "media_1787683482860.png"
        if src.exists() and src.stat().st_size > 0:
            try:
                shutil.copyfile(src, LOGO_IMAGE_FILE)
                logger.info(f"Copied StreamWave logo image from {src} to {LOGO_IMAGE_FILE}")
            except Exception as e:
                logger.error(f"Failed to copy logo image: {e}")


def ensure_favicon_assets():
    if LOGO_IMAGE_FILE.exists():
        favicon_png = IMAGES_DIR / "favicon.png"
        favicon_ico = PUBLIC_DIR / "favicon.ico"
        try:
            if not favicon_png.exists():
                shutil.copyfile(LOGO_IMAGE_FILE, favicon_png)
            if not favicon_ico.exists():
                shutil.copyfile(LOGO_IMAGE_FILE, favicon_ico)
        except Exception as e:
            logger.error(f"Failed to copy favicon: {e}")


ensure_video_preview_asset()
ensure_logo_asset()
ensure_favicon_assets()

# Vercel Blob Audio URL Environment Variable with local static fallback
DEFAULT_FALLBACK_AUDIO_URL = "/media/demo.wav"
BLOB_AUDIO_URL_ENV = os.getenv("STREAMWAVE_BLOB_URL") or os.getenv("VERCEL_BLOB_AUDIO_URL")


def load_media_catalogue() -> List[dict]:
    """Loads read-only media catalogue from data/media.json using pathlib."""
    if not DATA_FILE.exists():
        logger.error(f"Media catalogue file not found at {DATA_FILE}")
        return []

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        catalogue = json.load(f)

    active_blob_url = os.getenv("STREAMWAVE_BLOB_URL") or os.getenv("VERCEL_BLOB_AUDIO_URL")

    for item in catalogue:
        if item.get("type") == "music" and item.get("media_url") == DEFAULT_FALLBACK_AUDIO_URL and active_blob_url:
            item["media_url"] = active_blob_url.strip()

    return catalogue


# --- FastAPI Dependency for Access Control ---

async def verify_paid_session(request: Request) -> dict:
    """FastAPI reusable dependency enforcing signed demo-paid session cookie for protected catalogue APIs."""
    token = request.cookies.get("streamwave_session")
    session_data = verify_session_token(token) if token else None
    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Membership required. Please subscribe to access the StreamWave catalogue.",
        )
    return session_data


# --- Pydantic Validation Models ---

class HealthResponse(BaseModel):
    status: str = Field(..., json_schema_extra={"example": "ok"})
    platform: str = Field(..., json_schema_extra={"example": "StreamWave Serverless Media Platform"})
    environment: str = Field(..., json_schema_extra={"example": "Vercel Serverless"})
    blob_storage_configured: bool = Field(..., json_schema_extra={"example": False})
    timestamp: str = Field(..., json_schema_extra={"example": "2026-08-25T17:25:30Z"})


class MediaItem(BaseModel):
    id: str = Field(..., json_schema_extra={"example": "1"})
    title: str = Field(..., json_schema_extra={"example": "Cook Off"})
    artist_or_director: str = Field(..., json_schema_extra={"example": "Tomas Brickhill"})
    type: str = Field(..., json_schema_extra={"example": "movie"})
    genre: str = Field(..., json_schema_extra={"example": "Comedy"})
    year: int = Field(..., json_schema_extra={"example": 2017})
    duration: str = Field(..., json_schema_extra={"example": "1h 41m"})
    description: str = Field(...)
    cover_image: Optional[str] = None
    media_url: Optional[str] = None
    preview_url: Optional[str] = None


class PlayEventRequest(BaseModel):
    media_id: str = Field(..., min_length=1, max_length=50)
    session_id: Optional[str] = Field(default=None, max_length=100)
    client_timestamp: Optional[str] = Field(default=None, max_length=100)


class PlayEventDetail(BaseModel):
    media_id: str
    session_id: Optional[str] = None
    client_timestamp: Optional[str] = None
    server_timestamp: str
    media_title: str
    media_url_used: Optional[str] = None


class PlayEventResponse(BaseModel):
    status: str = "recorded"
    event: PlayEventDetail


class DemoPaymentRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=120, json_schema_extra={"example": "customer@example.co.zw"})
    method: str = Field(..., min_length=3, max_length=20, json_schema_extra={"example": "ecocash"})  # ecocash, visa, mastercard
    plan_id: Optional[str] = Field(default="streamwave-monthly", max_length=50, json_schema_extra={"example": "streamwave-monthly"})
    simulate_decline: Optional[bool] = Field(default=False, json_schema_extra={"example": False})


class DemoPaymentResponse(BaseModel):
    status: str = "approved"
    tx_ref: str
    email: str
    method: str
    plan: dict
    redirect_url: str = "/library"


class SessionInfoResponse(BaseModel):
    authenticated: bool
    email: Optional[str] = None
    plan: Optional[dict] = None


# --- FastAPI Application ---

app = FastAPI(
    title="StreamWave Serverless Media Platform API",
    description="FastAPI Backend for StreamWave Entertainment with Academic Payment Simulation & Session Access Control",
    version="2.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


# Security Response Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


# --- Public HTML Page Routes ---

@app.get("/", response_class=FileResponse, include_in_schema=False)
async def serve_landing_page():
    """Serves the public StreamWave landing page."""
    landing_file = PUBLIC_DIR / "index.html"
    if landing_file.exists():
        return FileResponse(str(landing_file))
    raise HTTPException(status_code=404, detail="Landing page not found")


@app.get("/checkout", response_class=FileResponse, include_in_schema=False)
async def serve_checkout_page():
    """Serves the simulated academic checkout page."""
    checkout_file = PUBLIC_DIR / "checkout.html"
    if checkout_file.exists():
        return FileResponse(str(checkout_file))
    raise HTTPException(status_code=404, detail="Checkout page not found")


@app.get("/library", response_class=FileResponse, include_in_schema=False)
async def serve_library_page():
    """Serves the paid member catalogue library page."""
    library_file = PUBLIC_DIR / "library.html"
    if library_file.exists():
        return FileResponse(str(library_file))
    raise HTTPException(status_code=404, detail="Library page not found")


# --- Public API Routes ---

@app.get("/api/health", response_model=HealthResponse, tags=["Health"])
async def get_health():
    """Returns platform health status, Vercel Blob configuration status, and serverless environment info."""
    active_blob = bool(os.getenv("STREAMWAVE_BLOB_URL") or os.getenv("VERCEL_BLOB_AUDIO_URL"))
    return HealthResponse(
        status="ok",
        platform="StreamWave Serverless Media Platform",
        environment="Vercel Serverless",
        blob_storage_configured=active_blob,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@app.get("/api/session", response_model=SessionInfoResponse, tags=["Session"])
async def get_session(request: Request):
    """Checks the active demo-paid member session status from signed HTTP-only cookie."""
    token = request.cookies.get("streamwave_session")
    session_data = verify_session_token(token) if token else None
    if session_data:
        return SessionInfoResponse(
            authenticated=True,
            email=session_data.get("email"),
            plan=SUBSCRIPTION_PLAN,
        )
    return SessionInfoResponse(authenticated=False, email=None, plan=None)


@app.post("/api/demo-payment", response_model=DemoPaymentResponse, status_code=status.HTTP_200_OK, tags=["Session"])
async def process_demo_payment(payload: DemoPaymentRequest, response: Response):
    """
    Validates simulated payment request (EcoCash, Visa, MasterCard). Supports both
    simulated approved and declined demonstration states. NEVER accepts or stores genuine financial data.
    """
    email = payload.email.strip().lower() if payload.email else ""
    if not email or "@" not in email or "." not in email:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A valid customer email address is required.",
        )

    method = payload.method.strip().lower() if payload.method else ""
    valid_methods = {"ecocash", "visa", "mastercard"}
    if method not in valid_methods:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid payment method. Supported methods: {', '.join(valid_methods)}",
        )

    server_ts = datetime.now(timezone.utc).isoformat()

    # Handle explicit simulated decline for demonstration testing
    if payload.simulate_decline:
        logger.info(
            json.dumps(
                {
                    "event_type": "demo_payment_declined",
                    "customer_email": email,
                    "payment_method": method,
                    "plan_id": SUBSCRIPTION_PLAN["id"],
                    "server_timestamp": server_ts,
                    "status": "declined",
                    "reason": "Simulated issuer decline test",
                }
            )
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Simulated payment decline: Card or mobile payment issuer rejected transaction.",
        )

    # Generate unique demonstration transaction reference for approval
    tx_ref = f"SW-DEMO-{int(time.time())}-{os.urandom(2).hex().upper()}"

    # Log structured JSON telemetry (strictly NO card/PIN/mobile numbers)
    logger.info(
        json.dumps(
            {
                "event_type": "demo_payment_approved",
                "tx_ref": tx_ref,
                "customer_email": email,
                "payment_method": method,
                "plan_id": SUBSCRIPTION_PLAN["id"],
                "price": SUBSCRIPTION_PLAN["price"],
                "server_timestamp": server_ts,
                "status": "approved",
            }
        )
    )

    # Create signed session token
    token = create_session_token(email)

    # Set secure HTTP-only session cookie (Secure flag enabled on Vercel production & HTTPS)
    is_secure_deployment = (
        os.getenv("VERCEL_ENV") == "production"
        or os.getenv("VERCEL") == "1"
        or os.getenv("HTTPS") == "on"
    )

    response.set_cookie(
        key="streamwave_session",
        value=token,
        max_age=86400 * 7,
        httponly=True,
        samesite="lax",
        secure=is_secure_deployment,
    )

    return DemoPaymentResponse(
        status="approved",
        tx_ref=tx_ref,
        email=email,
        method=method,
        plan=SUBSCRIPTION_PLAN,
        redirect_url="/library",
    )


@app.post("/api/logout", tags=["Session"])
async def logout(response: Response):
    """Clears the signed demo-paid member session cookie and logs out."""
    response.delete_cookie(key="streamwave_session", path="/")
    return {"status": "logged_out", "message": "Demo session cleared successfully."}


@app.post("/api/reset-demo", tags=["Session"])
async def reset_demo(response: Response):
    """Assessment control endpoint to reset member session state."""
    response.delete_cookie(key="streamwave_session", path="/")
    return {"status": "reset", "message": "Demonstration session reset successfully."}


# --- Protected API Routes (Requires Signed Session Cookie) ---

@app.get(
    "/api/media",
    response_model=List[MediaItem],
    dependencies=[Depends(verify_paid_session)],
    tags=["Media"],
)
async def get_media(
    query: Optional[str] = Query(default=None, max_length=100),
    type: Optional[str] = Query(default=None, max_length=20),
    genre: Optional[str] = Query(default=None, max_length=50),
):
    """Protected Endpoint: Retrieves media catalogue array for demo-paid members."""
    catalogue = load_media_catalogue()
    results = catalogue

    if type:
        target_type = type.strip().lower()
        results = [item for item in results if item.get("type", "").lower() == target_type]

    if genre:
        target_genre = genre.strip().lower()
        results = [item for item in results if item.get("genre", "").lower() == target_genre]

    if query:
        q = query.strip().lower()
        results = [
            item
            for item in results
            if q in item.get("title", "").lower()
            or q in item.get("artist_or_director", "").lower()
            or q in item.get("description", "").lower()
            or q in item.get("genre", "").lower()
        ]

    return results


@app.get(
    "/api/media/{media_id}",
    response_model=MediaItem,
    dependencies=[Depends(verify_paid_session)],
    tags=["Media"],
)
async def get_media_detail(media_id: str = PathParam(..., max_length=50)):
    """Protected Endpoint: Retrieves single media item detail by ID for demo-paid members."""
    catalogue = load_media_catalogue()
    for item in catalogue:
        if item.get("id") == media_id:
            return item
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Media item not found",
    )


@app.post(
    "/api/play-events",
    response_model=PlayEventResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verify_paid_session)],
    tags=["Playback Events"],
)
async def create_play_event(payload: PlayEventRequest):
    """Protected Endpoint: Logs structured playback telemetry event for demo-paid members."""
    catalogue = load_media_catalogue()
    media_item = next((item for item in catalogue if item.get("id") == payload.media_id), None)
    if not media_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media item not found",
        )

    server_ts = datetime.now(timezone.utc).isoformat()
    media_url = media_item.get("media_url", DEFAULT_FALLBACK_AUDIO_URL)

    event_detail = PlayEventDetail(
        media_id=payload.media_id,
        session_id=payload.session_id,
        client_timestamp=payload.client_timestamp,
        server_timestamp=server_ts,
        media_title=media_item.get("title", ""),
        media_url_used=media_url,
    )

    logger.info(
        json.dumps(
            {
                "event_type": "playback_started",
                "media_id": payload.media_id,
                "media_title": media_item.get("title", ""),
                "media_type": media_item.get("type", "unknown"),
                "media_url": media_url,
                "session_id": payload.session_id,
                "client_timestamp": payload.client_timestamp,
                "server_timestamp": server_ts,
            }
        )
    )

    return PlayEventResponse(status="recorded", event=event_detail)


# --- Static Files Mounting ---

if PUBLIC_DIR.exists():
    app.mount("/", StaticFiles(directory=str(PUBLIC_DIR), html=True), name="public")
