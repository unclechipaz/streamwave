import os
import sys
import time
from pathlib import Path

# Ensure root project directory is on sys.path for test runner imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest
from fastapi.testclient import TestClient
from app import app, create_session_token

client = TestClient(app)


# --- Helper for Authenticated Test Client ---

def get_auth_client(email: str = "member@streamwave.co.zw"):
    """Returns a TestClient instance with a valid demo-paid session cookie."""
    authenticated_client = TestClient(app)
    token = create_session_token(email)
    authenticated_client.cookies.set("streamwave_session", token)
    return authenticated_client


# --- Public Routes Tests ---

def test_health_endpoint():
    """Tests GET /api/health returns 200 OK and expected serverless metadata."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "StreamWave" in data["platform"]
    assert "environment" in data
    assert "blob_storage_configured" in data
    assert "timestamp" in data


def test_landing_page_publicly_accessible():
    """Tests GET / returns 200 OK and contains expected StreamWave landing heading."""
    response = client.get("/")
    assert response.status_code == 200
    assert "Zimbabwe’s stories, music and movies" in response.text
    assert "Stream from US$2.99 per month" in response.text


def test_checkout_page_publicly_accessible():
    """Tests GET /checkout returns 200 OK and contains academic payment warning banner."""
    response = client.get("/checkout")
    assert response.status_code == 200
    assert "ACADEMIC PAYMENT SIMULATION" in response.text
    assert "EcoCash" in response.text
    assert "Visa" in response.text
    assert "MasterCard" in response.text


def test_unpaid_user_cannot_access_protected_catalogue():
    """Tests GET /api/media without session cookie returns 401 Unauthorized."""
    response = client.get("/api/media")
    assert response.status_code == 401
    assert response.json()["detail"] == "Membership required. Please subscribe to access the StreamWave catalogue."


def test_unpaid_user_cannot_access_media_detail():
    """Tests GET /api/media/1 without session cookie returns 401 Unauthorized."""
    response = client.get("/api/media/1")
    assert response.status_code == 401


def test_unpaid_user_cannot_log_play_events():
    """Tests POST /api/play-events without session cookie returns 401 Unauthorized."""
    payload = {"media_id": "1", "session_id": "sess-test"}
    response = client.post("/api/play-events", json=payload)
    assert response.status_code == 401


# --- Security & Cookie Tampering Tests ---

def test_tampered_cookie_rejected():
    """Tests that a tampered or altered session cookie returns 401 Unauthorized."""
    tampered_client = TestClient(app)
    tampered_client.cookies.set("streamwave_session", "eyJlbWFpbCI6ImhhY2tlckBleGFtcGxlLmNvbSJ9.invalid_signature_hash")
    response = tampered_client.get("/api/media")
    assert response.status_code == 401


def test_expired_cookie_rejected():
    """Tests that an expired session token returns 401 Unauthorized."""
    expired_token = create_session_token("expired@streamwave.co.zw", expiry_seconds=-3600)
    expired_client = TestClient(app)
    expired_client.cookies.set("streamwave_session", expired_token)
    response = expired_client.get("/api/media")
    assert response.status_code == 401


def test_excessive_email_length_rejected():
    """Tests POST /api/demo-payment rejects email exceeding maximum allowed length."""
    long_email = "a" * 125 + "@example.com"
    payload = {"email": long_email, "method": "visa"}
    response = client.post("/api/demo-payment", json=payload)
    assert response.status_code == 422


# --- Payment Simulation Tests ---

def test_invalid_payment_method_rejected():
    """Tests POST /api/demo-payment returns 422 for unsupported payment method."""
    payload = {"email": "test@streamwave.co.zw", "method": "crypto"}
    response = client.post("/api/demo-payment", json=payload)
    assert response.status_code == 422
    assert "Invalid payment method" in response.json()["detail"]


def test_invalid_email_rejected():
    """Tests POST /api/demo-payment returns 422 for malformed email address."""
    payload = {"email": "invalidemail", "method": "ecocash"}
    response = client.post("/api/demo-payment", json=payload)
    assert response.status_code == 422
    assert "valid customer email address" in response.json()["detail"]


def test_ecocash_payment_simulation():
    """Tests successful EcoCash simulation sets signed session cookie and returns transaction reference."""
    payload = {"email": "ecocash.user@streamwave.co.zw", "method": "ecocash"}
    response = client.post("/api/demo-payment", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "approved"
    assert data["method"] == "ecocash"
    assert data["tx_ref"].startswith("SW-DEMO-")
    assert "streamwave_session" in response.cookies


def test_visa_payment_simulation():
    """Tests successful Visa simulation sets signed session cookie."""
    payload = {"email": "visa.user@streamwave.co.zw", "method": "visa"}
    response = client.post("/api/demo-payment", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "approved"
    assert data["method"] == "visa"
    assert "streamwave_session" in response.cookies


def test_mastercard_payment_simulation():
    """Tests successful MasterCard simulation sets signed session cookie."""
    payload = {"email": "mastercard.user@streamwave.co.zw", "method": "mastercard"}
    response = client.post("/api/demo-payment", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "approved"
    assert data["method"] == "mastercard"
    assert "streamwave_session" in response.cookies


def test_simulated_payment_decline_rejected():
    """Tests POST /api/demo-payment with simulate_decline=True returns HTTP 400 and does NOT set session cookie."""
    payload = {
        "email": "decline.user@streamwave.co.zw",
        "method": "visa",
        "simulate_decline": True,
    }
    response = client.post("/api/demo-payment", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert "Simulated payment decline" in data["detail"]
    assert "streamwave_session" not in response.cookies


# --- Authenticated Paid Member Session Tests ---

def test_session_info_unauthenticated():
    """Tests GET /api/session for unauthenticated request."""
    response = client.get("/api/session")
    assert response.status_code == 200
    data = response.json()
    assert data["authenticated"] is False
    assert data["email"] is None


def test_session_info_authenticated():
    """Tests GET /api/session for authenticated request returns email and plan details."""
    auth_client = get_auth_client("paidmember@streamwave.co.zw")
    response = auth_client.get("/api/session")
    assert response.status_code == 200
    data = response.json()
    assert data["authenticated"] is True
    assert data["email"] == "paidmember@streamwave.co.zw"
    assert data["plan"]["name"] == "StreamWave Monthly"


def test_demo_paid_user_can_access_protected_catalogue():
    """Tests that a paid member client can access GET /api/media."""
    auth_client = get_auth_client()
    response = auth_client.get("/api/media")
    assert response.status_code == 200
    items = response.json()
    assert isinstance(items, list)
    assert len(items) == 8


def test_demo_paid_user_can_access_media_detail():
    """Tests that a paid member client can access GET /api/media/1."""
    auth_client = get_auth_client()
    response = auth_client.get("/api/media/1")
    assert response.status_code == 200
    item = response.json()
    assert item["id"] == "1"
    assert item["title"] == "Cook Off"
    assert item["preview_url"] == "/media/streamwave-preview.mp4"


def test_demo_paid_user_can_log_play_events():
    """Tests that a paid member client can post to /api/play-events."""
    auth_client = get_auth_client()
    payload = {
        "media_id": "1",
        "session_id": "sess-test-paid",
        "client_timestamp": "2026-08-25T21:00:00Z",
    }
    response = auth_client.post("/api/play-events", json=payload)
    assert response.status_code == 201
    assert response.json()["status"] == "recorded"


def test_logout_clears_session_access():
    """Tests POST /api/logout clears session cookie, revoking subsequent access."""
    auth_client = get_auth_client()
    assert auth_client.get("/api/media").status_code == 200

    logout_res = auth_client.post("/api/logout")
    assert logout_res.status_code == 200

    protected_res = auth_client.get("/api/media")
    assert protected_res.status_code == 401


def test_reset_demo_clears_session():
    """Tests POST /api/reset-demo clears session cookie."""
    auth_client = get_auth_client()
    reset_res = auth_client.post("/api/reset-demo")
    assert reset_res.status_code == 200
    assert auth_client.get("/api/media").status_code == 401


# --- Catalogue Search & Filtering Regression Tests ---

def test_media_search_filter_stream():
    """Regression test: GET /api/media with query=stream."""
    auth_client = get_auth_client()
    response = auth_client.get("/api/media?query=stream")
    assert response.status_code == 200
    items = response.json()
    assert len(items) > 0
    assert any("stream" in item["description"].lower() for item in items)


def test_media_type_filter_music():
    """Regression test: GET /api/media with type=music."""
    auth_client = get_auth_client()
    music_res = auth_client.get("/api/media?type=music")
    assert music_res.status_code == 200
    music = music_res.json()
    assert len(music) == 4
    assert all(item["type"] == "music" for item in music)


def test_media_type_filter_movie():
    """Regression test: GET /api/media with type=movie."""
    auth_client = get_auth_client()
    movie_res = auth_client.get("/api/media?type=movie")
    assert movie_res.status_code == 200
    movies = movie_res.json()
    assert len(movies) == 4
    assert all(item["type"] == "movie" for item in movies)
    assert all(item["preview_url"] == "/media/streamwave-preview.mp4" for item in movies)


def test_media_genre_filter():
    """Regression test: GET /api/media with genre filter."""
    auth_client = get_auth_client()
    response = auth_client.get("/api/genre=Zimdancehall")  # Handled safely by Pydantic query param or path
    response_valid = auth_client.get("/api/media?genre=Zimdancehall")
    assert response_valid.status_code == 200
    items = response_valid.json()
    assert len(items) > 0
    assert all(item["genre"] == "Zimdancehall" for item in items)


def test_local_fallback_when_no_blob_env(monkeypatch):
    """Regression test: Clean fallback to /media/demo.wav for music."""
    monkeypatch.delenv("STREAMWAVE_BLOB_URL", raising=False)
    monkeypatch.delenv("VERCEL_BLOB_AUDIO_URL", raising=False)

    auth_client = get_auth_client()
    response = auth_client.get("/api/media/5")  # Disappear (music)
    assert response.status_code == 200
    item = response.json()
    assert item["media_url"] == "/media/demo.wav"
