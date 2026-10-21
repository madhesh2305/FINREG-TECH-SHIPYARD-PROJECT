"""
Single-process in-memory rate limiting service for security-sensitive workflows.

Design & Deployment Notes:
- Enforces sliding-window rate limits per target account and per client source IP.
- Uses one-way cryptographic SHA-256 digests for rate-limit keys to avoid retaining
  or leaking plaintext email addresses or client IP addresses in memory.
- Bounded memory footprint with automatic expiration cleanup and capacity eviction.
- Note: This is an in-memory, single-process implementation suitable for monolithic
  deployments and prototypes. It does not provide distributed synchronization across
  multiple independent application worker nodes.
"""
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

# Maximum distinct hashed keys tracked before forced eviction of oldest items
MAX_TRACKED_KEYS = 2000

# Storage for sliding window request timestamps: { hashed_key: [timestamp1, timestamp2, ...] }
_RATE_LIMIT_STORE: Dict[str, List[datetime]] = {}

def _hash_identifier(prefix: str, value: str) -> str:
    """Generates a non-reversible SHA-256 keyed digest for privacy-preserving rate tracking."""
    digest = hashlib.sha256(f"{prefix}:{value.strip().lower()}".encode("utf-8")).hexdigest()[:16]
    return f"{prefix}:{digest}"

def check_password_reset_rate_limit(
    email: str,
    client_ip: Optional[str] = None,
    max_account_requests: int = 5,
    max_ip_requests: int = 20,
    window_minutes: int = 15
) -> bool:
    """
    Evaluates rate limits for password recovery requests.
    Enforces dual-key bounds:
      1. Per-account limit: Prevents targeted credential stuffing and mail bombing.
      2. Per-IP source limit: Prevents distributed scraping of unknown accounts.
    Returns True if request is within allowable limits, False if rate-limited.
    """
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(minutes=window_minutes)

    # 1. Bounded cleanup: Remove global keys that have no recent timestamps
    if len(_RATE_LIMIT_STORE) > MAX_TRACKED_KEYS:
        expired_keys = [
            k for k, timestamps in _RATE_LIMIT_STORE.items()
            if not timestamps or timestamps[-1] < cutoff
        ]
        for k in expired_keys:
            _RATE_LIMIT_STORE.pop(k, None)

    # 2. Check per-account rate limit
    account_key = _hash_identifier("acct", email)
    acct_timestamps = [ts for ts in _RATE_LIMIT_STORE.get(account_key, []) if ts > cutoff]
    if len(acct_timestamps) >= max_account_requests:
        _RATE_LIMIT_STORE[account_key] = acct_timestamps
        logger.warning("Password reset rate limit exceeded for account key %s", account_key)
        return False

    # 3. Check per-IP rate limit
    ip_key = _hash_identifier("src", client_ip or "127.0.0.1")
    ip_timestamps = [ts for ts in _RATE_LIMIT_STORE.get(ip_key, []) if ts > cutoff]
    if len(ip_timestamps) >= max_ip_requests:
        _RATE_LIMIT_STORE[ip_key] = ip_timestamps
        logger.warning("Password reset rate limit exceeded for IP key %s", ip_key)
        return False

    # 4. Record new request timestamp in both sliding windows
    acct_timestamps.append(now)
    _RATE_LIMIT_STORE[account_key] = acct_timestamps

    ip_timestamps.append(now)
    _RATE_LIMIT_STORE[ip_key] = ip_timestamps

    return True

def reset_rate_limiter() -> None:
    """Clears all rate limit state to guarantee clean test isolation."""
    _RATE_LIMIT_STORE.clear()
