#!/usr/bin/env python3
"""
Rate Limiter for Site Builder

Provides IP-based rate limiting, concurrent job limits, and
optional Cloudflare Turnstile verification.

All state is in-memory (resets on restart). This is intentional —
rate limits are short-lived and don't need persistence.
"""

import os
import time
from collections import defaultdict
from typing import Optional

import httpx
from fastapi import HTTPException, Request

# ---------------------------------------------------------------------------
# Configuration (from env vars with sane defaults)
# ---------------------------------------------------------------------------
# Max sites per IP per rolling window
RATE_LIMIT_MAX = int(os.environ.get("RATE_LIMIT_MAX", "5"))
RATE_LIMIT_WINDOW = int(os.environ.get("RATE_LIMIT_WINDOW", "3600"))  # seconds (1 hour)

# Max concurrent jobs per IP
MAX_CONCURRENT_PER_IP = int(os.environ.get("MAX_CONCURRENT_PER_IP", "1"))

# Global max concurrent jobs
MAX_CONCURRENT_GLOBAL = int(os.environ.get("MAX_CONCURRENT_GLOBAL", "10"))

# Cloudflare Turnstile (optional — disabled if not configured)
TURNSTILE_SECRET = os.environ.get("TURNSTILE_SECRET_KEY", "")
TURNSTILE_ENABLED = TURNSTILE_SECRET.startswith("0x")  # Real keys start with 0x
TURNSTILE_VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"

# ---------------------------------------------------------------------------
# In-memory state
# ---------------------------------------------------------------------------
# IP -> list of generation timestamps (for rate limiting)
_ip_timestamps: dict[str, list[float]] = defaultdict(list)

# IP -> set of active job_ids (for concurrent limit)
_ip_active_jobs: dict[str, set[str]] = defaultdict(set)

# All active job_ids (for global limit)
_global_active_jobs: set[str] = set()


def _get_client_ip(request: Request) -> str:
    """Extract client IP, respecting proxy headers."""
    # Railway/Vercel/Cloudflare set these headers
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()
    return request.client.host if request.client else "unknown"


def _cleanup_timestamps(ip: str) -> None:
    """Remove timestamps outside the rolling window."""
    cutoff = time.time() - RATE_LIMIT_WINDOW
    _ip_timestamps[ip] = [t for t in _ip_timestamps[ip] if t > cutoff]


def check_rate_limit(request: Request) -> str:
    """Check all rate limits. Returns client IP if allowed, raises HTTPException if not."""
    ip = _get_client_ip(request)

    # 1. Global concurrent limit
    if len(_global_active_jobs) >= MAX_CONCURRENT_GLOBAL:
        raise HTTPException(
            status_code=429,
            detail=f"Server is busy ({MAX_CONCURRENT_GLOBAL} sites generating simultaneously). Please try again in a minute.",
        )

    # 2. Per-IP concurrent limit
    if len(_ip_active_jobs[ip]) >= MAX_CONCURRENT_PER_IP:
        raise HTTPException(
            status_code=429,
            detail="You already have a site generating. Please wait for it to finish.",
        )

    # 3. Per-IP rate limit (rolling window)
    _cleanup_timestamps(ip)
    if len(_ip_timestamps[ip]) >= RATE_LIMIT_MAX:
        oldest = min(_ip_timestamps[ip])
        retry_after = int(oldest + RATE_LIMIT_WINDOW - time.time()) + 1
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit reached ({RATE_LIMIT_MAX} sites per hour). Try again in {retry_after // 60} minutes.",
            headers={"Retry-After": str(retry_after)},
        )

    return ip


def record_job_start(ip: str, job_id: str) -> None:
    """Record that a job has started for rate tracking."""
    _ip_timestamps[ip].append(time.time())
    _ip_active_jobs[ip].add(job_id)
    _global_active_jobs.add(job_id)


def record_job_end(job_id: str) -> None:
    """Record that a job has finished (success or failure)."""
    _global_active_jobs.discard(job_id)
    for ip_jobs in _ip_active_jobs.values():
        ip_jobs.discard(job_id)


async def verify_turnstile(token: Optional[str], request: Request) -> None:
    """Verify a Cloudflare Turnstile token. No-op if Turnstile is not configured."""
    if not TURNSTILE_ENABLED:
        return

    if not token:
        raise HTTPException(
            status_code=400,
            detail="Human verification required. Please complete the captcha.",
        )

    ip = _get_client_ip(request)

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            TURNSTILE_VERIFY_URL,
            data={
                "secret": TURNSTILE_SECRET,
                "response": token,
                "remoteip": ip,
            },
        )

    result = resp.json()
    if not result.get("success"):
        raise HTTPException(
            status_code=403,
            detail="Human verification failed. Please try again.",
        )


def get_rate_limit_status() -> dict:
    """Return current rate limit stats for health/monitoring."""
    return {
        "global_active_jobs": len(_global_active_jobs),
        "global_max": MAX_CONCURRENT_GLOBAL,
        "unique_ips_active": len([ip for ip, jobs in _ip_active_jobs.items() if jobs]),
        "rate_limit": f"{RATE_LIMIT_MAX} per {RATE_LIMIT_WINDOW}s",
        "turnstile_enabled": TURNSTILE_ENABLED,
    }
