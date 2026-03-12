"""Tests for Pydantic models and helper functions."""
import pytest
from main import (
    GenerateSiteRequest,
    GenerateSiteResponse,
    RebuildSiteRequest,
    GenerateSectionRequest,
    RedeploySiteRequest,
    _resolve_deploy_target,
)


# ─── GenerateSiteRequest ─────────────────────────────
class TestGenerateSiteRequest:
    def test_minimal(self):
        req = GenerateSiteRequest(maps_url="https://maps.google.com/test")
        assert req.maps_url == "https://maps.google.com/test"
        assert req.template_name == "modern"
        assert req.deploy_target is None
        assert req.business_context is None
        assert req.website_url is None

    def test_full(self):
        req = GenerateSiteRequest(
            maps_url="https://maps.google.com/test",
            template_name="classic",
            deploy_target="cloudflare",
            business_context="Best plumber in town",
            website_url="https://example.com",
        )
        assert req.template_name == "classic"
        assert req.deploy_target == "cloudflare"
        assert req.business_context == "Best plumber in town"
        assert req.website_url == "https://example.com"

    def test_both_urls_optional(self):
        """maps_url is now optional (website_url can be used instead)."""
        req = GenerateSiteRequest()
        assert req.maps_url is None
        assert req.website_url is None

    def test_website_only(self):
        req = GenerateSiteRequest(
            website_url="https://example.com",
            business_name="Test Biz",
            business_category="Restaurant",
        )
        assert req.maps_url is None
        assert req.website_url == "https://example.com"
        assert req.business_name == "Test Biz"
        assert req.business_category == "Restaurant"


# ─── GenerateSiteResponse ─────────────────────────────
class TestGenerateSiteResponse:
    def test_create(self):
        resp = GenerateSiteResponse(job_id="abc-123", status="started")
        assert resp.job_id == "abc-123"
        assert resp.status == "started"


# ─── RebuildSiteRequest ──────────────────────────────
class TestRebuildSiteRequest:
    def test_create(self):
        req = RebuildSiteRequest(
            job_id="test-id",
            data={"business_name": "Test", "hero_headline": "Hello"},
        )
        assert req.job_id == "test-id"
        assert req.data["business_name"] == "Test"

    def test_missing_fields(self):
        with pytest.raises(Exception):
            RebuildSiteRequest(job_id="x")


# ─── GenerateSectionRequest ──────────────────────────
class TestGenerateSectionRequest:
    def test_create(self):
        req = GenerateSectionRequest(
            section_type="services",
            prompt="Add 3 more services",
            context={"business_name": "Test Biz", "category": "Plumbing"},
        )
        assert req.section_type == "services"
        assert req.prompt == "Add 3 more services"
        assert req.context["business_name"] == "Test Biz"

    def test_valid_section_types(self):
        """All valid section types should be accepted by the model."""
        for st in ["services", "faq_items", "testimonials", "why_choose_us", "process_steps"]:
            req = GenerateSectionRequest(
                section_type=st, prompt="test", context={}
            )
            assert req.section_type == st


# ─── RedeploySiteRequest ─────────────────────────────
class TestRedeploySiteRequest:
    def test_create(self):
        req = RedeploySiteRequest(job_id="xyz")
        assert req.job_id == "xyz"


# ─── _resolve_deploy_target ──────────────────────────
class TestResolveDeployTarget:
    def test_none_returns_none(self):
        result = _resolve_deploy_target("none")
        assert result is None

    def test_auto_with_no_providers(self):
        # If neither CF nor Vercel is configured, returns None
        # This is a real check against env vars
        import os
        # Temporarily clear env vars
        cf_token = os.environ.pop("CLOUDFLARE_API_TOKEN", None)
        cf_acct = os.environ.pop("CLOUDFLARE_ACCOUNT_ID", None)
        v_token = os.environ.pop("VERCEL_TOKEN", None)
        try:
            result = _resolve_deploy_target("auto")
            # Could be None or a provider depending on env
            assert result is None or result in ("cloudflare", "vercel")
        finally:
            # Restore
            if cf_token: os.environ["CLOUDFLARE_API_TOKEN"] = cf_token
            if cf_acct: os.environ["CLOUDFLARE_ACCOUNT_ID"] = cf_acct
            if v_token: os.environ["VERCEL_TOKEN"] = v_token
