"""Shared test fixtures for the Site Builder backend."""
import pytest
from httpx import AsyncClient, ASGITransport
from main import app, jobs


@pytest.fixture
async def client():
    """Async HTTP client wired to the FastAPI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture(autouse=True)
def clean_jobs():
    """Clear the in-memory jobs dict before and after each test."""
    jobs.clear()
    yield
    jobs.clear()


@pytest.fixture
def sample_job_id():
    """Create a sample completed job in the jobs dict and return its ID."""
    import uuid
    from datetime import datetime

    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "job_id": job_id,
        "status": "completed",
        "maps_url": "https://maps.google.com/?cid=12345",
        "template_name": "modern",
        "created_at": datetime.now().isoformat(),
        "step": "done",
        "error": None,
        "result": {
            "html": "<html><body><h1>Test Site</h1></body></html>",
            "business_name": "Test Business",
            "title": "Test Business - Home",
            "build_dir": "/tmp/test-build-dir",
            "dist_path": "/tmp/test-build-dir/dist",
            "deploy_url": None,
            "deploy_provider": None,
            "content": {"hero_headline": "Welcome"},
            "business_data": {"name": "Test Business", "category": "Test"},
        },
    }
    return job_id


@pytest.fixture
def sample_editable_data():
    """Sample data.json payload for editor tests."""
    return {
        "business_name": "Test Business",
        "category": "Plumbing",
        "hero_headline": "Expert Plumbing Services",
        "hero_subheadline": "Available 24/7",
        "about_text": "We are a trusted plumbing company.",
        "color_primary": "#2563eb",
        "color_secondary": "#1e40af",
        "font_heading": "Inter",
        "font_body": "Inter",
        "phone": "(555) 123-4567",
        "email": "info@test.com",
        "address": "123 Main St",
        "services": [
            {"name": "Pipe Repair", "description": "Fix any pipe", "icon_suggestion": "wrench"},
            {"name": "Drain Cleaning", "description": "Clear clogs fast", "icon_suggestion": "bolt"},
        ],
        "faq_items": [
            {"question": "Do you offer emergency?", "answer": "Yes, 24/7."},
        ],
        "testimonials": [
            {"author": "John D.", "rating": 5, "text": "Great work!"},
        ],
        "why_choose_us": [
            {"title": "Licensed", "description": "Fully licensed.", "icon_key": "shield"},
        ],
        "process_steps": [
            {"step_number": 1, "title": "Call Us", "description": "Give us a call.", "icon_key": "phone"},
        ],
    }
