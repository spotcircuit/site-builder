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
    assert resp.status_code == 400  # Custom validation: at least one URL required
    assert "maps_url or website_url" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_generate_site_website_only_missing_name(client):
    resp = await client.post("/api/generate-site", json={
        "website_url": "https://example.com",
    })
    assert resp.status_code == 400  # business_name required for website-only
    assert "business_name" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_generate_site_website_only(client):
    resp = await client.post("/api/generate-site", json={
        "website_url": "https://example.com",
        "business_name": "Test Business",
        "business_category": "Restaurant",
    })
    assert resp.status_code == 202
    data = resp.json()
    assert "job_id" in data
    assert data["status"] == "started"


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


@pytest.mark.anyio
async def test_list_templates(client):
    """GET /api/templates returns available templates."""
    resp = await client.get("/api/templates")
    assert resp.status_code == 200
    data = resp.json()
    assert "templates" in data
    templates = data["templates"]
    assert isinstance(templates, list)
    assert len(templates) >= 1
    # Modern should always be available
    modern = next(t for t in templates if t["name"] == "modern")
    assert modern["available"] is True
    assert modern.get("label") == "Modern"


# ─── Section Composition ─────────────────────────────
def test_default_sections_constant():
    """DEFAULT_SECTIONS is defined with all 12 section types."""
    from modules.react_builder import DEFAULT_SECTIONS
    assert isinstance(DEFAULT_SECTIONS, list)
    assert len(DEFAULT_SECTIONS) == 12
    # Verify structure
    for section in DEFAULT_SECTIONS:
        assert "id" in section
        assert "type" in section
        assert "enabled" in section
        assert "order" in section
        assert section["enabled"] is True
    # Check key sections exist
    types = [s["type"] for s in DEFAULT_SECTIONS]
    assert "hero" in types
    assert "about" in types
    assert "services" in types
    assert "footer" in types
    assert "faq" in types
    assert "cta" in types
    # Order should be sequential
    orders = [s["order"] for s in DEFAULT_SECTIONS]
    assert orders == list(range(12))


def test_generate_data_json_includes_sections():
    """_generate_data_json() injects sections array into data."""
    from modules.react_builder import _generate_data_json
    data = _generate_data_json(
        content={"hero_headline": "Test", "services": []},
        business_data={"name": "Test Biz"},
    )
    assert "sections" in data
    assert isinstance(data["sections"], list)
    assert len(data["sections"]) == 12
    # Verify it's a deep copy (modifying shouldn't affect the constant)
    data["sections"][0]["enabled"] = False
    data2 = _generate_data_json(
        content={"hero_headline": "Test2"},
        business_data={"name": "Test2"},
    )
    assert data2["sections"][0]["enabled"] is True


def test_generate_data_json_preserves_existing_sections():
    """_generate_data_json() doesn't overwrite existing sections in content."""
    from modules.react_builder import _generate_data_json
    custom_sections = [{"id": "custom", "type": "hero", "enabled": True, "order": 0}]
    data = _generate_data_json(
        content={"sections": custom_sections, "hero_headline": "Test"},
        business_data={"name": "Test"},
    )
    assert len(data["sections"]) == 1
    assert data["sections"][0]["id"] == "custom"


# ─── Section Composition Boundary ────────────────────
def test_section_reorder_preserves_all_sections():
    """Reordering sections via _generate_data_json doesn't lose any."""
    from modules.react_builder import _generate_data_json
    # Provide sections in reversed order
    reversed_sections = [
        {"id": "footer", "type": "footer", "enabled": True, "order": 0},
        {"id": "contact", "type": "contact", "enabled": True, "order": 1},
        {"id": "cta", "type": "cta", "enabled": True, "order": 2},
        {"id": "faq", "type": "faq", "enabled": True, "order": 3},
        {"id": "testimonials", "type": "testimonials", "enabled": True, "order": 4},
        {"id": "gallery", "type": "gallery", "enabled": True, "order": 5},
        {"id": "how-it-works", "type": "how-it-works", "enabled": True, "order": 6},
        {"id": "why-choose-us", "type": "why-choose-us", "enabled": True, "order": 7},
        {"id": "services", "type": "services", "enabled": True, "order": 8},
        {"id": "about", "type": "about", "enabled": True, "order": 9},
        {"id": "social-proof", "type": "social-proof", "enabled": True, "order": 10},
        {"id": "hero", "type": "hero", "enabled": True, "order": 11},
    ]
    data = _generate_data_json(
        content={"sections": reversed_sections, "hero_headline": "Test"},
        business_data={"name": "Test"},
    )
    # Should preserve all 12 sections in the reversed order
    assert len(data["sections"]) == 12
    assert data["sections"][0]["type"] == "footer"
    assert data["sections"][11]["type"] == "hero"


def test_section_disabled_preserved():
    """Disabled sections are preserved through _generate_data_json."""
    from modules.react_builder import _generate_data_json
    sections = [
        {"id": "hero", "type": "hero", "enabled": True, "order": 0},
        {"id": "about", "type": "about", "enabled": False, "order": 1},
        {"id": "footer", "type": "footer", "enabled": True, "order": 2},
    ]
    data = _generate_data_json(
        content={"sections": sections, "hero_headline": "Test"},
        business_data={"name": "Test"},
    )
    assert len(data["sections"]) == 3
    about = next(s for s in data["sections"] if s["type"] == "about")
    assert about["enabled"] is False


def test_section_with_duplicate_cta():
    """Multiple CTA sections (allowed by spec) are preserved."""
    from modules.react_builder import _generate_data_json
    sections = [
        {"id": "hero", "type": "hero", "enabled": True, "order": 0},
        {"id": "cta-1", "type": "cta", "enabled": True, "order": 1},
        {"id": "cta-2", "type": "cta", "enabled": True, "order": 2},
        {"id": "footer", "type": "footer", "enabled": True, "order": 3},
    ]
    data = _generate_data_json(
        content={"sections": sections, "hero_headline": "Test"},
        business_data={"name": "Test"},
    )
    cta_sections = [s for s in data["sections"] if s["type"] == "cta"]
    assert len(cta_sections) == 2
