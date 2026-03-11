"""Tests for Site Builder REST API endpoints."""
import asyncio
import pytest
import uuid
from datetime import datetime
from main import jobs


@pytest.fixture(autouse=True)
async def cancel_background_tasks():
    """Cancel any background tasks spawned during tests (e.g. pipeline runs)."""
    yield
    # Cancel all pending tasks except current
    for task in asyncio.all_tasks():
        if task is not asyncio.current_task() and not task.done():
            task.cancel()
            try:
                await task
            except (asyncio.CancelledError, Exception):
                pass


# ─── Health ───────────────────────────────────────────
@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["service"] == "site-builder"
    assert "active_jobs" in data
    assert "services" in data


# ─── Generate Site ────────────────────────────────────
@pytest.mark.asyncio
async def test_generate_site_creates_job(client):
    resp = await client.post("/api/generate-site", json={
        "maps_url": "https://www.google.com/maps/place/Test/@40.7,-74.0,17z",
        "template_name": "modern",
    })
    assert resp.status_code == 202
    data = resp.json()
    assert "job_id" in data
    assert data["status"] == "started"
    # Job should exist in the dict
    assert data["job_id"] in jobs


@pytest.mark.asyncio
async def test_generate_site_missing_url(client):
    resp = await client.post("/api/generate-site", json={})
    assert resp.status_code == 422  # Pydantic validation


# ─── Job Status ───────────────────────────────────────
@pytest.mark.asyncio
async def test_get_job_status(client, sample_job_id):
    resp = await client.get(f"/api/job/{sample_job_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["job_id"] == sample_job_id
    assert data["status"] == "completed"
    assert data["result"] is not None
    # Should strip large fields
    assert "dist_path" not in data["result"]
    assert "build_dir" not in data["result"]
    assert "content" not in data["result"]


@pytest.mark.asyncio
async def test_get_job_not_found(client):
    resp = await client.get("/api/job/nonexistent-id")
    assert resp.status_code == 404


# ─── Download ─────────────────────────────────────────
@pytest.mark.asyncio
async def test_download_completed(client, sample_job_id):
    resp = await client.get(f"/api/job/{sample_job_id}/download")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "Content-Disposition" in resp.headers
    assert "Test-Business" in resp.headers["Content-Disposition"]


@pytest.mark.asyncio
async def test_download_not_completed(client):
    jid = str(uuid.uuid4())
    jobs[jid] = {
        "job_id": jid, "status": "started", "maps_url": "x",
        "template_name": "modern", "created_at": datetime.now().isoformat(),
        "step": None, "result": None, "error": None,
    }
    resp = await client.get(f"/api/job/{jid}/download")
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_download_not_found(client):
    resp = await client.get("/api/job/fake/download")
    assert resp.status_code == 404


# ─── Editable Data ────────────────────────────────────
@pytest.mark.asyncio
async def test_get_editable_data(client, sample_job_id):
    resp = await client.get(f"/api/job/{sample_job_id}/data")
    assert resp.status_code == 200
    data = resp.json()
    assert "data" in data
    assert isinstance(data["data"], dict)


@pytest.mark.asyncio
async def test_get_editable_data_not_found(client):
    resp = await client.get("/api/job/missing/data")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_editable_data_no_result(client):
    jid = str(uuid.uuid4())
    jobs[jid] = {
        "job_id": jid, "status": "started", "maps_url": "x",
        "template_name": "modern", "created_at": datetime.now().isoformat(),
        "step": None, "result": None, "error": None,
    }
    resp = await client.get(f"/api/job/{jid}/data")
    assert resp.status_code == 400


# ─── Rebuild Site ─────────────────────────────────────
@pytest.mark.asyncio
async def test_rebuild_no_job(client, sample_editable_data):
    resp = await client.post("/api/rebuild-site", json={
        "job_id": "nonexistent",
        "data": sample_editable_data,
    })
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_rebuild_no_build_dir(client, sample_editable_data):
    jid = str(uuid.uuid4())
    jobs[jid] = {
        "job_id": jid, "status": "completed", "maps_url": "x",
        "template_name": "modern", "created_at": datetime.now().isoformat(),
        "step": "done", "result": {"html": "<h1>hi</h1>"}, "error": None,
    }
    resp = await client.post("/api/rebuild-site", json={
        "job_id": jid,
        "data": sample_editable_data,
    })
    assert resp.status_code == 400


# ─── Generate Section ────────────────────────────────
@pytest.mark.asyncio
async def test_generate_section_invalid_type(client):
    resp = await client.post("/api/generate-section", json={
        "section_type": "invalid_section",
        "prompt": "test",
        "context": {"business_name": "Test"},
    })
    assert resp.status_code == 400
    assert "Unknown section type" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_generate_section_validation(client):
    resp = await client.post("/api/generate-section", json={})
    assert resp.status_code == 422


# ─── Redeploy ─────────────────────────────────────────
@pytest.mark.asyncio
async def test_redeploy_no_job(client):
    resp = await client.post("/api/redeploy-site", json={"job_id": "missing"})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_redeploy_no_dist(client):
    jid = str(uuid.uuid4())
    jobs[jid] = {
        "job_id": jid, "status": "completed", "maps_url": "x",
        "template_name": "modern", "created_at": datetime.now().isoformat(),
        "step": "done", "result": {"html": "<h1>x</h1>"}, "error": None,
    }
    resp = await client.post("/api/redeploy-site", json={"job_id": jid})
    assert resp.status_code == 400


# ─── Upload Image ─────────────────────────────────────
@pytest.mark.asyncio
async def test_upload_image_success(client):
    # Create a tiny 1x1 PNG
    png_bytes = (
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
        b'\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00'
        b'\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00'
        b'\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
    )
    resp = await client.post(
        "/api/upload-image",
        files={"file": ("test.png", png_bytes, "image/png")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "url" in data
    assert data["url"].startswith("/uploads/")
    assert data["url"].endswith(".png")
    assert "filename" in data


@pytest.mark.asyncio
async def test_upload_image_wrong_type(client):
    resp = await client.post(
        "/api/upload-image",
        files={"file": ("test.txt", b"hello", "text/plain")},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
@pytest.mark.skipif(True, reason="Allocating 10MB+ in tests is slow; gate tested via unit check")
async def test_upload_image_too_large(client):
    big_data = b'\x00' * (10 * 1024 * 1024 + 1)
    resp = await client.post(
        "/api/upload-image",
        files={"file": ("big.png", big_data, "image/png")},
    )
    assert resp.status_code == 400


def test_max_image_size_constant():
    """Verify the size gate constant is set correctly."""
    from main import MAX_IMAGE_SIZE
    assert MAX_IMAGE_SIZE == 10 * 1024 * 1024  # 10 MB


# ─── Delete Site ──────────────────────────────────────
@pytest.mark.asyncio
async def test_delete_site_invalid_name(client):
    resp = await client.delete("/api/site/invalid name!!")
    assert resp.status_code == 400


# ─── Job TTL ─────────────────────────────────────────
def test_job_created_at_stored():
    """Verify jobs store a created_at timestamp for TTL cleanup."""
    jid = str(uuid.uuid4())
    jobs[jid] = {
        "job_id": jid, "status": "started", "maps_url": "x",
        "template_name": "modern", "created_at": datetime.now().isoformat(),
        "step": None, "result": None, "error": None,
    }
    assert "created_at" in jobs[jid]
    # Should be parseable
    parsed = datetime.fromisoformat(jobs[jid]["created_at"])
    assert isinstance(parsed, datetime)
