import pytest
from fastapi.testclient import TestClient
from app.core.config import settings
from app.core.rate_limit import reset_rate_limits
from app.main import app

client = TestClient(app)


def test_security_headers_present_on_endpoints():
    """Verify standard defensive HTTP headers are attached to all API responses."""
    response = client.get("/health")
    assert response.status_code == 200

    headers = response.headers
    assert headers.get("x-content-type-options") == "nosniff"
    assert headers.get("x-frame-options") == "DENY"
    assert headers.get("referrer-policy") == "strict-origin-when-cross-origin"
    assert "microphone=()" in headers.get("permissions-policy", "")
    assert "camera=()" in headers.get("permissions-policy", "")
    assert "geolocation=()" in headers.get("permissions-policy", "")


def test_security_headers_present_on_root_endpoint():
    """Verify security headers are attached to root service index endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers.get("x-content-type-options") == "nosniff"
    assert response.headers.get("x-frame-options") == "DENY"


def test_cors_allowed_origins():
    """Verify that requests from authorized frontend origins receive CORS headers."""
    response = client.options(
        "/api/v1/auth/login",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
        }
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert response.headers.get("access-control-allow-credentials") == "true"


def test_cors_disallowed_origin():
    """Verify that unauthorized external origins do NOT receive CORS allow headers."""
    response = client.options(
        "/api/v1/auth/login",
        headers={
            "Origin": "http://evil-attacker.example.com",
            "Access-Control-Request-Method": "POST",
        }
    )
    # Untrusted origin should NOT be echoed back as allowed
    allow_origin = response.headers.get("access-control-allow-origin")
    assert allow_origin != "http://evil-attacker.example.com"
    assert allow_origin != "*"


def test_rate_limiting_enforcement_and_429_response():
    """Verify that exceeding rate limit triggers 429 Too Many Requests with standard headers."""
    reset_rate_limits()
    original_state = settings.RATE_LIMIT_ENABLED
    original_max = settings.RATE_LIMIT_LOGIN_MAX
    try:
        settings.RATE_LIMIT_ENABLED = True
        settings.RATE_LIMIT_LOGIN_MAX = 3
        settings.RATE_LIMIT_LOGIN_WINDOW_SECONDS = 60

        test_ip = "192.168.100.55"
        headers = {"X-Forwarded-For": test_ip}
        payload = {"email": "test_brute_force@example.com", "password": "wrongpassword"}

        # Request 1, 2, 3 should proceed to normal auth logic (401 invalid creds)
        for i in range(3):
            res = client.post("/api/v1/auth/login", json=payload, headers=headers)
            assert res.status_code != 429, f"Request {i+1} unexpectedly throttled"

        # Request 4 should be throttled with 429
        res_throttled = client.post("/api/v1/auth/login", json=payload, headers=headers)
        assert res_throttled.status_code == 429
        data = res_throttled.json()
        assert "Too many requests" in data.get("detail", "")
        assert "retry-after" in res_throttled.headers
        assert res_throttled.headers.get("x-ratelimit-limit") == "3"
        assert res_throttled.headers.get("x-ratelimit-remaining") == "0"

        # A different IP address should NOT be throttled
        different_headers = {"X-Forwarded-For": "192.168.100.56"}
        res_other_ip = client.post("/api/v1/auth/login", json=payload, headers=different_headers)
        assert res_other_ip.status_code != 429

    finally:
        settings.RATE_LIMIT_ENABLED = original_state
        settings.RATE_LIMIT_LOGIN_MAX = original_max
        reset_rate_limits()


def test_ai_microservice_cors_wildcard_elimination():
    """Verify that abc-shield-ai configuration does not contain wildcard in cors_origins."""
    from pathlib import Path
    import sys

    ai_root = Path(__file__).resolve().parent.parent.parent / "abc-shield-ai"
    settings_file = ai_root / "config" / "settings.py"
    assert settings_file.exists(), f"Settings file not found at {settings_file}"

    content = settings_file.read_text(encoding="utf-8")
    # Verify "*" is not inside cors_origins list
    assert '"*"' not in content, "Wildcard '*' must not be present in abc-shield-ai cors_origins"
