#!/usr/bin/env python3
"""
Site Builder Backend
FastAPI server for generating business websites from Google Maps URLs.

Pipeline: Maps URL parsing -> Business scraping -> AI content generation -> HTML rendering
All progress is streamed to connected clients via WebSocket.
"""

import asyncio
import json
import logging
import os
import re
import traceback
import uuid
from datetime import datetime
from typing import Any, Optional
from urllib.parse import urlparse

from dotenv import load_dotenv
from pathlib import Path as FilePath

from fastapi import FastAPI, HTTPException, Response, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from modules.maps_url_parser import parse_maps_url, ParsedMapsUrl
from modules.maps_scraper import scrape_business_from_maps, BusinessData
from modules.website_scraper import scrape_website, WebsiteData
from modules.site_generator import generate_site, generate_site_content, GeneratedSite, SiteContent
from modules.react_builder import build_react_site, rebuild_react_site, cleanup_build, ReactBuildResult, get_available_templates
from modules.vercel_deployer import deploy_to_vercel, is_vercel_configured
from modules.cloudflare_deployer import deploy_to_cloudflare, is_cloudflare_configured
from modules.image_generator import generate_site_images, is_gemini_configured
from modules.websocket_manager import get_websocket_manager

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------
load_dotenv()

logger = logging.getLogger(__name__)

PORT = int(os.getenv("SITE_BUILDER_PORT", "9405"))
HOST = os.getenv("SITE_BUILDER_HOST", "0.0.0.0")

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Site Builder API",
    version="1.0.0",
    description="Generate business websites from Google Maps URLs",
)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(_cleanup_expired_jobs())


# CORS -- permissive for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5177",
        "http://127.0.0.1:5177",
        "http://localhost:*",
        "http://127.0.0.1:*",
        "*",  # Allow all origins during development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket manager (singleton)
ws_manager = get_websocket_manager()

# ---------------------------------------------------------------------------
# Uploads directory for user-uploaded images
# ---------------------------------------------------------------------------
UPLOADS_DIR = FilePath(__file__).parent / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

# ---------------------------------------------------------------------------
# In-memory job storage
# ---------------------------------------------------------------------------
jobs: dict[str, dict[str, Any]] = {}

# ---------------------------------------------------------------------------
# Persistent error log
# ---------------------------------------------------------------------------
ERROR_LOG_PATH = FilePath(__file__).parent / "error_log.jsonl"


def _log_error(job_id: str, error_message: str, error_details: str, context: dict | None = None) -> None:
    """Append an error entry to the persistent JSONL error log."""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "job_id": job_id,
        "error": error_message,
        "traceback": error_details,
    }
    if context:
        entry["context"] = context
    try:
        with open(ERROR_LOG_PATH, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as log_exc:
        logger.warning("Failed to write error log: %s", log_exc)

# Persistent deploy log
# ---------------------------------------------------------------------------
DEPLOY_LOG_PATH = FilePath(__file__).parent / "deploy_log.jsonl"


def _log_deploy(job_id: str, business_name: str, deploy_url: str, provider: str,
                template: str, extra: dict | None = None) -> None:
    """Append a successful deploy entry to the persistent JSONL deploy log."""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "job_id": job_id,
        "business_name": business_name,
        "deploy_url": deploy_url,
        "provider": provider,
        "template": template,
    }
    if extra:
        entry.update(extra)
    try:
        with open(DEPLOY_LOG_PATH, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as log_exc:
        logger.warning("Failed to write deploy log: %s", log_exc)


# Job TTL: auto-delete undeployed jobs after 3 days
JOB_TTL_SECONDS = 3 * 24 * 60 * 60  # 3 days


async def _cleanup_expired_jobs():
    """Background task: delete expired undeployed jobs and their build dirs."""
    while True:
        await asyncio.sleep(3600)  # Check every hour
        now = datetime.now()
        expired = []
        for jid, job in jobs.items():
            created_str = job.get("created_at")
            if not created_str:
                continue
            try:
                created = datetime.fromisoformat(created_str)
            except (TypeError, ValueError):
                continue
            age = (now - created).total_seconds()
            # Keep deployed sites longer (7 days), undeployed 3 days
            is_deployed = bool(job.get("result", {}).get("deploy_url"))
            ttl = JOB_TTL_SECONDS * 2 if is_deployed else JOB_TTL_SECONDS
            if age > ttl:
                expired.append(jid)
        for jid in expired:
            job = jobs.pop(jid, None)
            if job:
                build_dir = job.get("result", {}).get("build_dir")
                if build_dir:
                    try:
                        cleanup_build(build_dir)
                    except Exception:
                        pass
                try:
                    age_hrs = (now - datetime.fromisoformat(job["created_at"])).total_seconds() / 3600
                except Exception:
                    age_hrs = -1
                logger.info("Cleaned up expired job %s (age: %.1f hours)", jid, age_hrs)
        if expired:
            logger.info("Cleaned up %d expired jobs", len(expired))


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------
class GenerateSiteRequest(BaseModel):
    """Request body for the site generation endpoint.

    Accepts either a Google Maps URL or any website URL.
    - maps_url: Google Maps link (triggers full Maps scraping pipeline)
    - website_url: Any business website URL (scrapes website directly)
    At least one of maps_url or website_url must be provided.
    When using website_url without maps_url, business_name is required.
    """

    maps_url: Optional[str] = None
    template_name: str = "modern"
    deploy_target: Optional[str] = None  # "vercel", "cloudflare", "auto", or None
    business_context: Optional[str] = None  # User-provided business description
    website_url: Optional[str] = None  # Business website URL for scraping
    business_name: Optional[str] = None  # Required when using website_url without maps_url
    business_category: Optional[str] = None  # Optional category hint for website-only generation


class GenerateSiteResponse(BaseModel):
    """Immediate response returned when a generation job is created."""

    job_id: str
    status: str


class RebuildSiteRequest(BaseModel):
    """Request body for rebuilding a site with edited data."""

    job_id: str
    data: dict  # The full data.json payload


class GenerateSectionRequest(BaseModel):
    """Request body for AI-generating new section content."""

    section_type: str  # "services", "faq_items", "testimonials", "why_choose_us", "process_steps"
    prompt: str  # User's instruction
    context: dict  # Business context (name, category, existing content summary)


class RedeploySiteRequest(BaseModel):
    """Request body for re-deploying an edited site."""

    job_id: str


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------
def _resolve_deploy_target(deploy_target: Optional[str]) -> Optional[str]:
    """Determine which hosting provider to use."""
    if deploy_target == "none":
        return None
    if deploy_target == "cloudflare" and is_cloudflare_configured():
        return "cloudflare"
    if deploy_target == "vercel" and is_vercel_configured():
        return "vercel"
    if deploy_target in (None, "auto"):
        if is_cloudflare_configured():
            return "cloudflare"
        if is_vercel_configured():
            return "vercel"
    return None


async def run_generation_pipeline(
    job_id: str,
    maps_url: Optional[str],
    template_name: str,
    deploy_target: Optional[str] = None,
    business_context: Optional[str] = None,
    website_url: Optional[str] = None,
    business_name: Optional[str] = None,
    business_category: Optional[str] = None,
) -> None:
    """
    Execute the full site-generation pipeline for a given job.

    Supports two modes:
    - **Maps mode**: maps_url provided — full Google Maps scraping pipeline
    - **Website mode**: website_url only — scrapes website directly, skips Maps

    Steps:
        1. Parse URL / identify source
        2. Scrape business profile (Maps or website)
        3. Generate website content via Claude AI
        4. Build React site from templates
        5. Deploy to hosting (Cloudflare Pages / Vercel)

    Progress is broadcast to subscribed WebSocket clients for this job.
    """

    try:
        # Brief pause to let the client's WebSocket subscribe message arrive
        # (the frontend sends subscribe immediately after receiving job_id)
        await asyncio.sleep(0.5)

        is_website_only = not maps_url and website_url
        website_data: Optional[WebsiteData] = None

        if is_website_only:
            # ── WEBSITE-ONLY MODE ───────────────────────────────────────
            # Skip Maps parsing/scraping, go straight to website scrape
            jobs[job_id]["status"] = "scraping_website"
            jobs[job_id]["step"] = "scraping_website"
            await ws_manager.broadcast_step(
                step="parsing_url",
                status="started",
                message=f"Analyzing website: {website_url}",
                data={"job_id": job_id, "website_url": website_url},
            )
            await ws_manager.broadcast_step(
                step="parsing_url",
                status="completed",
                message=f"Website URL detected: {business_name or 'Business'}",
                data={"job_id": job_id},
            )

            # Scrape the website
            await ws_manager.broadcast_step(
                step="scraping_profile",
                status="started",
                message=f"Scraping website: {website_url}",
                data={"job_id": job_id},
            )

            try:
                website_data = await scrape_website(website_url)
            except Exception as ws_exc:
                logger.warning("Website scrape failed: %s", ws_exc)
                website_data = WebsiteData(url=website_url)

            # Build a minimal BusinessData from website scrape + user input
            scraped_name = (
                website_data.title
                or business_name
                or urlparse(website_url).hostname
                or "Business"
            )
            effective_name = business_name or scraped_name

            business_data = BusinessData(
                name=effective_name,
                website=website_url,
                category=business_category or None,
                address=website_data.contact_info.get("address") if website_data else None,
                phone=website_data.contact_info.get("phone") if website_data else None,
                email=website_data.contact_info.get("email") if website_data else None,
                hours=website_data.hours if website_data else None,
                services=website_data.services if website_data and website_data.services else None,
                photos=website_data.images[:10] if website_data and website_data.images else None,
                description=website_data.about_text if website_data else None,
            )

            # Log franchise/confidence detection
            if website_data and website_data.contact_confidence == "low":
                await ws_manager.broadcast_step(
                    step="scraping_profile",
                    status="progress",
                    message=f"Multiple locations detected ({len(website_data.all_locations)} addresses). Contact info may need verification.",
                    data={"job_id": job_id},
                )

            await ws_manager.broadcast_step(
                step="scraping_profile",
                status="completed",
                message=f"Scraped website for: {effective_name}",
                data={"job_id": job_id, "business_name": effective_name},
            )

        else:
            # ── MAPS MODE (original flow) ───────────────────────────────
            # Step 1: Parse Maps URL
            jobs[job_id]["status"] = "parsing_url"
            jobs[job_id]["step"] = "parsing_url"
            await ws_manager.broadcast_step(
                step="parsing_url",
                status="started",
                message="Parsing Google Maps URL...",
                data={"job_id": job_id, "maps_url": maps_url},
            )

            parsed_url: ParsedMapsUrl = await parse_maps_url(maps_url)

            await ws_manager.broadcast_step(
                step="parsing_url",
                status="completed",
                message=f"Parsed URL for: {parsed_url.business_name or 'Unknown business'}",
                data={
                    "job_id": job_id,
                    "business_name": parsed_url.business_name,
                    "place_id": parsed_url.place_id,
                },
            )

            # Step 2: Scrape business profile from Maps
            jobs[job_id]["status"] = "scraping_profile"
            jobs[job_id]["step"] = "scraping_profile"
            await ws_manager.broadcast_step(
                step="scraping_profile",
                status="started",
                message="Scraping business profile from Google Maps...",
                data={"job_id": job_id},
            )

            async def _scraper_callback(data: dict) -> None:
                await ws_manager.broadcast_step(
                    step="scraping_profile",
                    status="progress",
                    message=data.get("message", ""),
                    data={"job_id": job_id, "sub_step": data.get("step", "")},
                )

            business_data: BusinessData = await scrape_business_from_maps(
                place_id=parsed_url.place_id,
                cid=parsed_url.cid,
                business_name=parsed_url.business_name,
                raw_url=parsed_url.raw_url,
                callback=_scraper_callback,
            )

            await ws_manager.broadcast_step(
                step="scraping_profile",
                status="completed",
                message=f"Scraped profile for: {business_data.name}",
                data={"job_id": job_id, "business_name": business_data.name},
            )

        # ── Step 2.5: Scrape the business website for branding ──────────
        # (Skip if we already scraped in website-only mode)
        if not is_website_only:
            # Use user-provided website URL if given, otherwise fall back to Maps data
            effective_website = website_url or business_data.website
            if website_url and not business_data.website:
                business_data.website = website_url  # Store for downstream use
        else:
            effective_website = None  # Already scraped above

        if effective_website:
            try:
                await ws_manager.broadcast_step(
                    step="scraping_website",
                    status="started",
                    message=f"Scraping business website: {effective_website}",
                    data={"job_id": job_id},
                )
                website_data = await scrape_website(effective_website)
                await ws_manager.broadcast_step(
                    step="scraping_website",
                    status="completed",
                    message=(
                        f"Got {len(website_data.images)} images, "
                        f"{len(website_data.brand_colors)} colors, "
                        f"{len(website_data.social_links)} social links, "
                        f"{len(website_data.subpages_scraped)} subpages from website"
                    ),
                    data={"job_id": job_id},
                )
            except Exception as exc:
                logger.warning("Website scrape failed (non-fatal): %s", exc)
                await ws_manager.broadcast_step(
                    step="scraping_website",
                    status="completed",
                    message="Website scraping skipped (couldn't access site)",
                    data={"job_id": job_id},
                )

        # ── Step 3: Generate content via Claude ─────────────────────────
        jobs[job_id]["status"] = "generating_content"
        jobs[job_id]["step"] = "generating_content"
        await ws_manager.broadcast_step(
            step="generating_content",
            status="started",
            message="Generating website content with AI...",
            data={"job_id": job_id},
        )

        async def _generator_callback(message: str) -> None:
            await ws_manager.broadcast_step(
                step="generating_content",
                status="progress",
                message=message,
                data={"job_id": job_id},
            )

        biz_dict = business_data.model_dump()
        # Merge website scrape data so the AI can use branding, about text, etc.
        if website_data:
            # Backfill Maps data gaps from website scrape
            if not business_data.phone and website_data.contact_info.get("phone"):
                business_data.phone = website_data.contact_info["phone"]
            if not business_data.email and website_data.contact_info.get("email"):
                business_data.email = website_data.contact_info["email"]
            if not business_data.hours and website_data.hours:
                business_data.hours = website_data.hours
            if not business_data.address and website_data.contact_info.get("address"):
                business_data.address = website_data.contact_info["address"]
            # Re-dump after backfill so biz_dict has the updated values
            biz_dict = business_data.model_dump()
            biz_dict["website_data"] = website_data.model_dump()
            # Thread franchise/confidence metadata
            biz_dict["contact_confidence"] = website_data.contact_confidence
            biz_dict["is_franchise"] = website_data.is_franchise
            biz_dict["all_locations"] = website_data.all_locations
        if not website_data:
            biz_dict["contact_confidence"] = "high"  # Maps-only = always high confidence
            biz_dict["is_franchise"] = False
            biz_dict["all_locations"] = []
        # Maps data is location-specific — always high confidence
        if not is_website_only:
            biz_dict["contact_confidence"] = "high"
            biz_dict["is_franchise"] = False
        # Add user-provided business context
        if business_context:
            biz_dict["user_context"] = business_context
        content: SiteContent = await generate_site_content(
            business_data=biz_dict,
            callback=_generator_callback,
        )

        # Use AI-inferred category if scraper didn't find one
        content_dict = content.model_dump()
        inferred_cat = content_dict.get("inferred_category", "")
        if not business_data.category and inferred_cat:
            business_data.category = inferred_cat
            biz_dict["category"] = inferred_cat

        await ws_manager.broadcast_step(
            step="generating_content",
            status="completed",
            message="AI content generation complete.",
            data={"job_id": job_id},
        )

        # ── Step 3.5: Generate AI images (if Gemini configured) ───────
        generated_images = None
        if is_gemini_configured():
            jobs[job_id]["status"] = "generating_images"
            jobs[job_id]["step"] = "generating_images"
            await ws_manager.broadcast_step(
                step="generating_images",
                status="started",
                message="Generating AI images for website...",
                data={"job_id": job_id},
            )

            async def _image_callback(message: str) -> None:
                await ws_manager.broadcast_step(
                    step="generating_images",
                    status="progress",
                    message=message,
                    data={"job_id": job_id},
                )

            try:
                has_photos = bool(business_data.photos and len(business_data.photos) > 0)
                generated_images = await generate_site_images(
                    business_name=business_data.name,
                    category=business_data.category or "",
                    hero_keyword=content.hero_image_keyword,
                    has_photos=has_photos,
                    callback=_image_callback,
                )

                await ws_manager.broadcast_step(
                    step="generating_images",
                    status="completed",
                    message=f"Generated {len(generated_images.images)} AI images.",
                    data={"job_id": job_id},
                )
            except Exception as img_exc:
                print(f"[Pipeline] Image generation failed (non-fatal): {img_exc}")
                await ws_manager.broadcast_step(
                    step="generating_images",
                    status="completed",
                    message=f"Image generation skipped: {img_exc}",
                    data={"job_id": job_id},
                )

        # ── Step 4: Build React site ────────────────────────────────────
        jobs[job_id]["status"] = "building_site"
        jobs[job_id]["step"] = "building_site"
        await ws_manager.broadcast_step(
            step="building_site",
            status="started",
            message="Building React site from templates...",
            data={"job_id": job_id},
        )

        async def _build_callback(message: str) -> None:
            await ws_manager.broadcast_step(
                step="building_site",
                status="progress",
                message=message,
                data={"job_id": job_id},
            )

        build_result: ReactBuildResult = await build_react_site(
            content=content.model_dump(),
            business_data=biz_dict,
            job_id=job_id,
            template_name=template_name,
            callback=_build_callback,
            generated_images=generated_images.model_dump() if generated_images else None,
        )

        # Store result (include business_data for editor rebuild)
        jobs[job_id]["result"] = {
            "html": build_result.index_html,
            "title": content.seo_title,
            "business_name": business_data.name,
            "template_name": template_name,
            "generated_at": datetime.now().isoformat(),
            "dist_path": build_result.dist_path,
            "build_dir": build_result.build_dir,
            "content": content.model_dump(),
            "business_data": biz_dict,
            "deploy_url": None,
            "deploy_provider": None,
            # SEO & local ranking data for frontend display
            "seo": {
                "seo_title": content.seo_title,
                "seo_description": content.seo_description,
                "og_title": content.og_title,
                "og_description": content.og_description,
                "rating": business_data.rating,
                "review_count": business_data.review_count,
                "has_phone": bool(business_data.phone),
                "has_address": bool(business_data.address),
                "has_website": bool(business_data.website),
                "has_hours": bool(business_data.hours),
                "has_photos": bool(business_data.photos),
                "has_reviews": bool(business_data.reviews),
                "category": business_data.category or "",
                "real_review_count": len(business_data.reviews) if business_data.reviews else 0,
            },
        }

        await ws_manager.broadcast_step(
            step="building_site",
            status="completed",
            message="React site built successfully.",
            data={"job_id": job_id},
        )

        # ── Step 5: Deploy to hosting ───────────────────────────────────
        resolved_target = _resolve_deploy_target(deploy_target)

        if resolved_target:
            jobs[job_id]["status"] = "deploying"
            jobs[job_id]["step"] = "deploying"
            await ws_manager.broadcast_step(
                step="deploying",
                status="started",
                message=f"Deploying to {resolved_target.title()}...",
                data={"job_id": job_id, "provider": resolved_target},
            )

            async def _deploy_callback(message: str) -> None:
                await ws_manager.broadcast_step(
                    step="deploying",
                    status="progress",
                    message=message,
                    data={"job_id": job_id},
                )

            try:
                from pathlib import Path

                dist_path = Path(build_result.dist_path)

                deploy_result = None

                if resolved_target == "cloudflare":
                    try:
                        deploy_result = await deploy_to_cloudflare(
                            dist_path=dist_path,
                            business_name=business_data.name,
                            job_id=job_id,
                            callback=_deploy_callback,
                        )
                    except Exception as cf_exc:
                        print(f"[Pipeline] Cloudflare deploy failed, trying Vercel: {cf_exc}")
                        await _deploy_callback(f"Cloudflare failed, falling back to Vercel...")
                        if is_vercel_configured():
                            deploy_result = await deploy_to_vercel(
                                dist_path=dist_path,
                                business_name=business_data.name,
                                job_id=job_id,
                                callback=_deploy_callback,
                            )
                elif resolved_target == "vercel":
                    try:
                        deploy_result = await deploy_to_vercel(
                            dist_path=dist_path,
                            business_name=business_data.name,
                            job_id=job_id,
                            callback=_deploy_callback,
                        )
                    except Exception as v_exc:
                        print(f"[Pipeline] Vercel deploy failed, trying Cloudflare: {v_exc}")
                        await _deploy_callback(f"Vercel failed, falling back to Cloudflare...")
                        if is_cloudflare_configured():
                            deploy_result = await deploy_to_cloudflare(
                                dist_path=dist_path,
                                business_name=business_data.name,
                                job_id=job_id,
                                callback=_deploy_callback,
                            )

                if deploy_result:
                    jobs[job_id]["result"]["deploy_url"] = deploy_result.url
                    jobs[job_id]["result"]["deploy_provider"] = deploy_result.provider

                    _log_deploy(
                        job_id=job_id,
                        business_name=business_data.name,
                        deploy_url=deploy_result.url,
                        provider=deploy_result.provider,
                        template=template_name,
                    )

                    await ws_manager.broadcast_step(
                        step="deploying",
                        status="completed",
                        message=f"Deployed to {deploy_result.url}",
                        data={"job_id": job_id, "url": deploy_result.url},
                    )
                else:
                    raise RuntimeError("Both deploy providers failed")

            except Exception as deploy_exc:
                print(f"[Pipeline] Deploy failed (non-fatal): {deploy_exc}")
                await ws_manager.broadcast_step(
                    step="deploying",
                    status="completed",
                    message=f"Deploy skipped: {deploy_exc}",
                    data={"job_id": job_id},
                )

        # ── Step 6: Broadcast completion ────────────────────────────────
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["completed_at"] = datetime.now().isoformat()
        await ws_manager.broadcast_site_ready(
            {
                "job_id": job_id,
                "title": content.seo_title,
                "business_name": business_data.name,
                "template_name": template_name,
                "deploy_url": jobs[job_id]["result"].get("deploy_url"),
                "deploy_provider": jobs[job_id]["result"].get("deploy_provider"),
                "seo": jobs[job_id]["result"].get("seo"),
            }
        )

    except Exception as exc:
        error_message = str(exc)
        error_details = traceback.format_exc()
        logger.error("[Pipeline] Error in job %s: %s\n%s", job_id, error_message, error_details)

        # Persist to error log
        _log_error(job_id, error_message, error_details, context={
            "maps_url": maps_url,
            "website_url": website_url,
            "business_name": business_name,
            "template": template_name,
            "step": jobs[job_id].get("status", "unknown"),
        })

        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = error_message
        jobs[job_id]["error_details"] = error_details
        jobs[job_id]["failed_at"] = datetime.now().isoformat()

        await ws_manager.broadcast_error(
            error_message=f"Site generation failed: {error_message}",
            details={"job_id": job_id, "traceback": error_details},
            job_id=job_id,
        )


# ---------------------------------------------------------------------------
# REST endpoints
# ---------------------------------------------------------------------------
@app.post(
    "/api/generate-site",
    response_model=GenerateSiteResponse,
    status_code=202,
)
async def generate_site_endpoint(request: GenerateSiteRequest):
    """
    Start an asynchronous site generation job.

    Accepts either a Google Maps URL or any website URL.
    Scrapes business data, generates content with Claude, and renders HTML.
    Progress is streamed over the ``/ws`` WebSocket endpoint.

    Returns immediately with a ``job_id`` that can be polled via
    ``GET /api/job/{job_id}``.
    """
    # Validate: at least one URL must be provided
    if not request.maps_url and not request.website_url:
        raise HTTPException(
            status_code=400,
            detail="Either maps_url or website_url must be provided",
        )

    # For website-only mode, business_name is required
    if not request.maps_url and request.website_url and not request.business_name:
        raise HTTPException(
            status_code=400,
            detail="business_name is required when using website_url without maps_url",
        )

    job_id = str(uuid.uuid4())

    jobs[job_id] = {
        "job_id": job_id,
        "status": "started",
        "maps_url": request.maps_url,
        "website_url": request.website_url,
        "template_name": request.template_name,
        "created_at": datetime.now().isoformat(),
        "step": None,
        "result": None,
        "error": None,
    }

    asyncio.create_task(
        run_generation_pipeline(
            job_id=job_id,
            maps_url=request.maps_url,
            template_name=request.template_name,
            deploy_target=request.deploy_target,
            business_context=request.business_context,
            website_url=request.website_url,
            business_name=request.business_name,
            business_category=request.business_category,
        )
    )

    return GenerateSiteResponse(job_id=job_id, status="started")


@app.get("/api/job/{job_id}")
async def get_job_status(job_id: str):
    """
    Poll the current status of a site generation job.

    Returns the job's status, current step, and result (when complete).
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    job = jobs[job_id]
    result = job.get("result")
    # Strip large fields from polling response
    safe_result = None
    if result:
        safe_result = {
            k: v for k, v in result.items()
            if k not in ("dist_path", "build_dir", "content")
        }
    return {
        "job_id": job["job_id"],
        "status": job["status"],
        "step": job.get("step"),
        "maps_url": job.get("maps_url"),
        "template_name": job.get("template_name"),
        "created_at": job.get("created_at"),
        "completed_at": job.get("completed_at"),
        "error": job.get("error"),
        "result": safe_result,
    }


@app.get("/api/job/{job_id}/download")
async def download_generated_site(job_id: str):
    """
    Download the generated HTML file for a completed job.

    Returns the rendered HTML with ``Content-Disposition`` set for download.
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    job = jobs[job_id]

    if job["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Job is not completed yet. Current status: {job['status']}",
        )

    result = job.get("result")
    if not result or not result.get("html"):
        raise HTTPException(
            status_code=500,
            detail="Job completed but no HTML was generated.",
        )

    html_content = result["html"]
    business_name = result.get("business_name", "site")
    # Sanitise for filename
    safe_name = "".join(c if c.isalnum() or c in "-_ " else "" for c in business_name)
    safe_name = safe_name.strip().replace(" ", "-") or "generated-site"

    return Response(
        content=html_content,
        media_type="text/html",
        headers={
            "Content-Disposition": f'attachment; filename="{safe_name}.html"',
        },
    )


@app.delete("/api/site/{project_name}")
async def delete_deployed_site(project_name: str):
    """Delete a deployed site from Cloudflare Pages or Vercel."""
    import httpx

    token = (os.environ.get("CLOUDFLARE_API_TOKEN") or "").strip()
    account_id = (os.environ.get("CLOUDFLARE_ACCOUNT_ID") or "").strip()

    if not token or not account_id:
        raise HTTPException(status_code=500, detail="Cloudflare not configured")

    # Sanitize project name to prevent path traversal
    if not re.match(r'^[a-z0-9-]+$', project_name):
        raise HTTPException(status_code=400, detail="Invalid project name")

    api_url = (
        f"https://api.cloudflare.com/client/v4/accounts/{account_id}"
        f"/pages/projects/{project_name}"
    )
    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.delete(api_url, headers=headers)
        data = resp.json()

    if data.get("success"):
        return {"status": "deleted", "project_name": project_name}

    errors = data.get("errors", [])
    # Already gone is fine
    if any(e.get("code") == 8000007 for e in errors):
        return {"status": "already_deleted", "project_name": project_name}

    raise HTTPException(status_code=500, detail=f"Delete failed: {errors}")


# ---------------------------------------------------------------------------
# Editor endpoints
# ---------------------------------------------------------------------------
@app.post("/api/rebuild-site")
async def rebuild_site_endpoint(request: RebuildSiteRequest):
    """Rebuild a site with updated data.json from the editor.

    Re-uses the existing build directory (skips template copy + npm install),
    writes updated data.json, re-runs npm build, returns new HTML.
    """
    if request.job_id not in jobs:
        raise HTTPException(status_code=404, detail=f"Job not found: {request.job_id}")

    job = jobs[request.job_id]
    result = job.get("result")
    if not result or not result.get("build_dir"):
        raise HTTPException(status_code=400, detail="Job has no build directory (may have been cleaned up)")

    build_dir = result["build_dir"]

    try:
        build_result = await rebuild_react_site(
            data=request.data,
            build_dir=build_dir,
            template_name=job.get("template_name", "modern"),
        )

        # Update stored result
        result["html"] = build_result.index_html
        result["dist_path"] = build_result.dist_path
        # Update stored content fields from the edited data
        result["title"] = request.data.get("seo_title", result.get("title", ""))
        result["business_name"] = request.data.get("business_name", result.get("business_name", ""))

        return {"html": build_result.index_html, "status": "rebuilt"}

    except Exception as exc:
        _log_error(request.job_id, f"Rebuild failed: {exc}", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Rebuild failed: {exc}")


@app.post("/api/generate-section")
async def generate_section_endpoint(request: GenerateSectionRequest):
    """Generate new content items for a specific section using Claude AI.

    Returns a list of items that can be appended to the section array.
    """
    from modules.site_generator import _get_anthropic_client

    section_prompts = {
        "services": {
            "instruction": "Generate new services/offerings for this business.",
            "format": '[{"name": "string", "description": "string (2 sentences)", "icon_suggestion": "icon-name"}]',
            "icons": "wrench, heart, shield-check, chart-bar, clock, map-pin, star, truck, camera, paint-brush, cog, bolt, sparkles, fire, cube, scissors, phone, home, check-circle, globe, users, briefcase",
        },
        "faq_items": {
            "instruction": "Generate FAQ items for this business.",
            "format": '[{"question": "string", "answer": "string (2-3 sentences)"}]',
            "icons": "",
        },
        "testimonials": {
            "instruction": "Generate realistic sample testimonials for this business. Prefix author names with [Sample].",
            "format": '[{"author": "[Sample] Name", "rating": 5, "text": "string (2-3 sentences)"}]',
            "icons": "",
        },
        "why_choose_us": {
            "instruction": "Generate differentiator items for this business.",
            "format": '[{"title": "string", "description": "string (1-2 sentences)", "icon_key": "icon-name"}]',
            "icons": "wrench, heart, shield-check, chart-bar, clock, star, sparkles, check-circle, globe, users",
        },
        "process_steps": {
            "instruction": "Generate how-it-works process steps for this business.",
            "format": '[{"step_number": 1, "title": "string", "description": "string (1-2 sentences)", "icon_key": "icon-name"}]',
            "icons": "check-circle, clock, star, sparkles, globe, users, briefcase",
        },
    }

    if request.section_type not in section_prompts:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown section type: {request.section_type}. Valid: {list(section_prompts.keys())}",
        )

    spec = section_prompts[request.section_type]
    business_name = request.context.get("business_name", "the business")
    category = request.context.get("category", "")

    icon_instruction = f"\nUse icon names from: {spec['icons']}" if spec["icons"] else ""

    system_prompt = (
        f"You generate website section content for business websites. "
        f"Return ONLY a valid JSON array (no markdown, no explanation). "
        f"Format: {spec['format']}{icon_instruction}"
    )

    user_prompt = (
        f"{spec['instruction']}\n\n"
        f"Business: {business_name}\n"
        f"Category: {category}\n"
        f"User request: {request.prompt}\n\n"
        f"Return a JSON array with the requested items."
    )

    try:
        client = _get_anthropic_client()
        response = await client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )

        raw_text = response.content[0].text.strip()

        # Parse JSON array from response
        import json as json_module

        # Try direct parse
        try:
            items = json_module.loads(raw_text)
        except json_module.JSONDecodeError:
            # Try extracting from markdown fences
            fence_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", raw_text, re.DOTALL)
            if fence_match:
                items = json_module.loads(fence_match.group(1).strip())
            else:
                bracket_match = re.search(r"\[.*\]", raw_text, re.DOTALL)
                if bracket_match:
                    items = json_module.loads(bracket_match.group(0))
                else:
                    raise ValueError("Could not parse AI response as JSON array")

        if not isinstance(items, list):
            items = [items]

        # Auto-number process steps
        if request.section_type == "process_steps":
            for i, item in enumerate(items):
                item["step_number"] = i + 1

        return {"items": items, "section_type": request.section_type}

    except Exception as exc:
        _log_error("generate-section", f"AI generation failed: {exc}", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"AI generation failed: {exc}")


@app.post("/api/redeploy-site")
async def redeploy_site_endpoint(request: RedeploySiteRequest):
    """Re-deploy an edited site using the existing dist/ directory."""
    if request.job_id not in jobs:
        raise HTTPException(status_code=404, detail=f"Job not found: {request.job_id}")

    job = jobs[request.job_id]
    result = job.get("result")
    if not result or not result.get("dist_path"):
        raise HTTPException(status_code=400, detail="No built site to deploy")

    from pathlib import Path

    dist_path = Path(result["dist_path"])
    if not dist_path.exists():
        raise HTTPException(status_code=400, detail="Build directory no longer exists")

    business_name = result.get("business_name", "site")

    resolved_target = _resolve_deploy_target("auto")
    if not resolved_target:
        raise HTTPException(status_code=500, detail="No deploy provider configured")

    try:
        deploy_result = None
        if resolved_target == "cloudflare":
            try:
                deploy_result = await deploy_to_cloudflare(
                    dist_path=dist_path,
                    business_name=business_name,
                    job_id=request.job_id,
                )
            except Exception:
                if is_vercel_configured():
                    deploy_result = await deploy_to_vercel(
                        dist_path=dist_path,
                        business_name=business_name,
                        job_id=request.job_id,
                    )
        elif resolved_target == "vercel":
            try:
                deploy_result = await deploy_to_vercel(
                    dist_path=dist_path,
                    business_name=business_name,
                    job_id=request.job_id,
                )
            except Exception:
                if is_cloudflare_configured():
                    deploy_result = await deploy_to_cloudflare(
                        dist_path=dist_path,
                        business_name=business_name,
                        job_id=request.job_id,
                    )

        if deploy_result:
            result["deploy_url"] = deploy_result.url
            result["deploy_provider"] = deploy_result.provider
            return {
                "deploy_url": deploy_result.url,
                "deploy_provider": deploy_result.provider,
                "status": "deployed",
            }

        raise RuntimeError("All deploy providers failed")

    except HTTPException:
        raise
    except Exception as exc:
        _log_error(request.job_id, f"Deploy failed: {exc}", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Deploy failed: {exc}")


@app.get("/api/job/{job_id}/data")
async def get_job_editable_data(job_id: str):
    """Get the editable data.json payload for a completed job.

    Used by the editor to populate the editing panel.
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    job = jobs[job_id]
    result = job.get("result")
    if not result:
        raise HTTPException(status_code=400, detail="Job has no result yet")

    content = result.get("content", {})
    business_data = result.get("business_data", {})

    # Reconstruct the data.json payload
    from modules.react_builder import _generate_data_json

    data = _generate_data_json(content, business_data)
    return {"data": data}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "site-builder",
        "version": "1.1.0",
        "websocket_connections": len(ws_manager.active_connections),
        "active_jobs": len(jobs),
        "timestamp": datetime.now().isoformat(),
        "services": {
            "anthropic": bool(os.environ.get("ANTHROPIC_API_KEY")),
            "cloudflare": is_cloudflare_configured(),
            "vercel": is_vercel_configured(),
            "gemini": is_gemini_configured(),
        },
    }


# ---------------------------------------------------------------------------
# Error Log
# ---------------------------------------------------------------------------
@app.get("/api/errors")
async def get_errors(limit: int = 50):
    """Return recent errors from the persistent error log (newest first)."""
    if not ERROR_LOG_PATH.exists():
        return {"errors": [], "total": 0}
    try:
        lines = ERROR_LOG_PATH.read_text().strip().splitlines()
        entries = []
        for line in reversed(lines[-limit:]):
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return {"errors": entries, "total": len(lines)}
    except Exception as exc:
        raise HTTPException(500, f"Failed to read error log: {exc}")


@app.delete("/api/errors")
async def clear_errors():
    """Clear the error log."""
    if ERROR_LOG_PATH.exists():
        ERROR_LOG_PATH.unlink()
    return {"status": "cleared"}


# ---------------------------------------------------------------------------
# Deploy Log (successful site deployments)
# ---------------------------------------------------------------------------
@app.get("/api/sites")
async def get_sites(limit: int = 100):
    """Return recent successful deploys from the persistent deploy log (newest first)."""
    if not DEPLOY_LOG_PATH.exists():
        return {"sites": [], "total": 0}
    try:
        lines = DEPLOY_LOG_PATH.read_text().strip().splitlines()
        entries = []
        for line in reversed(lines[-limit:]):
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return {"sites": entries, "total": len(lines)}
    except Exception as exc:
        raise HTTPException(500, f"Failed to read deploy log: {exc}")


@app.delete("/api/sites")
async def clear_sites():
    """Clear the deploy log."""
    if DEPLOY_LOG_PATH.exists():
        DEPLOY_LOG_PATH.unlink()
    return {"status": "cleared"}


# ---------------------------------------------------------------------------
# Image Upload
# ---------------------------------------------------------------------------
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif", "image/svg+xml"}
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB


@app.post("/api/upload-image")
async def upload_image(file: UploadFile):
    """Upload an image file and return its URL."""
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(400, f"Unsupported image type: {file.content_type}")

    contents = await file.read()
    if len(contents) > MAX_IMAGE_SIZE:
        raise HTTPException(400, "Image too large (max 10 MB)")

    ext = file.filename.rsplit(".", 1)[-1] if file.filename and "." in file.filename else "jpg"
    filename = f"{uuid.uuid4().hex[:12]}.{ext}"
    filepath = UPLOADS_DIR / filename
    filepath.write_bytes(contents)

    # Return URL relative to API base so frontend can use it directly
    return {"url": f"/uploads/{filename}", "filename": filename}


# ---------------------------------------------------------------------------
# WebSocket endpoint
# ---------------------------------------------------------------------------
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time site generation progress.

    Clients connect here to receive step-by-step updates, progress
    percentages, and the final ``site_ready`` event.
    """
    await ws_manager.connect(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            if data:
                try:
                    message = json.loads(data)
                    if isinstance(message, dict):
                        msg_type = message.get("type", "unknown")
                        # Client subscribes to a job to receive scoped updates
                        if msg_type == "subscribe" and message.get("job_id"):
                            ws_manager.subscribe(websocket, message["job_id"])
                        else:
                            print(f"[WS] Received message type: {msg_type}")
                except json.JSONDecodeError:
                    # Plain text / keep-alive ping -- ignore
                    pass
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as exc:
        print(f"[WS] Connection error: {exc}")
        ws_manager.disconnect(websocket)


# ---------------------------------------------------------------------------
# Template Registry
# ---------------------------------------------------------------------------

@app.get("/api/templates")
async def list_templates():
    """Return available site templates with metadata."""
    return {"templates": get_available_templates()}


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    print(f"[Site Builder] Starting on {HOST}:{PORT}")
    uvicorn.run(app, host=HOST, port=PORT)
