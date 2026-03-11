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

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Response, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from modules.maps_url_parser import parse_maps_url, ParsedMapsUrl
from modules.maps_scraper import scrape_business_from_maps, BusinessData
from modules.website_scraper import scrape_website, WebsiteData
from modules.site_generator import generate_site, generate_site_content, GeneratedSite, SiteContent
from modules.react_builder import build_react_site, cleanup_build, ReactBuildResult
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
# In-memory job storage
# ---------------------------------------------------------------------------
jobs: dict[str, dict[str, Any]] = {}


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------
class GenerateSiteRequest(BaseModel):
    """Request body for the site generation endpoint."""

    maps_url: str
    template_name: str = "modern"
    deploy_target: Optional[str] = None  # "vercel", "cloudflare", "auto", or None


class GenerateSiteResponse(BaseModel):
    """Immediate response returned when a generation job is created."""

    job_id: str
    status: str


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
    maps_url: str,
    template_name: str,
    deploy_target: Optional[str] = None,
) -> None:
    """
    Execute the full site-generation pipeline for a given job.

    Steps:
        1. Parse the Google Maps URL into structured data.
        2. Scrape business profile information from Google Maps.
        3. Generate website content via Claude AI.
        4. Build React site from templates.
        5. Deploy to hosting (Cloudflare Pages / Vercel).

    Progress is broadcast to all connected WebSocket clients at every step.
    """

    try:
        # ── Step 1: Parse Maps URL ──────────────────────────────────────
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

        # ── Step 2: Scrape business profile ─────────────────────────────
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
        website_data: Optional[WebsiteData] = None
        if business_data.website:
            try:
                await ws_manager.broadcast_step(
                    step="scraping_website",
                    status="started",
                    message=f"Scraping business website: {business_data.website}",
                    data={"job_id": job_id},
                )
                website_data = await scrape_website(business_data.website)
                await ws_manager.broadcast_step(
                    step="scraping_website",
                    status="completed",
                    message=(
                        f"Got {len(website_data.images)} images, "
                        f"{len(website_data.brand_colors)} colors, "
                        f"{len(website_data.social_links)} social links from website"
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
            biz_dict["website_data"] = website_data.model_dump()
        content: SiteContent = await generate_site_content(
            business_data=biz_dict,
            callback=_generator_callback,
        )

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
            callback=_build_callback,
            generated_images=generated_images.model_dump() if generated_images else None,
        )

        # Store result
        jobs[job_id]["result"] = {
            "html": build_result.index_html,
            "title": content.seo_title,
            "business_name": business_data.name,
            "template_name": template_name,
            "generated_at": datetime.now().isoformat(),
            "dist_path": build_result.dist_path,
            "build_dir": build_result.build_dir,
            "content": content.model_dump(),
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
        print(f"[Pipeline] Error in job {job_id}: {error_message}\n{error_details}")

        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = error_message
        jobs[job_id]["failed_at"] = datetime.now().isoformat()

        await ws_manager.broadcast_error(
            error_message=f"Site generation failed: {error_message}",
            details={"job_id": job_id, "traceback": error_details},
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

    Parses the provided Google Maps URL, scrapes business data, generates
    content with Claude, and renders HTML.  Progress is streamed over the
    ``/ws`` WebSocket endpoint.

    Returns immediately with a ``job_id`` that can be polled via
    ``GET /api/job/{job_id}``.
    """
    job_id = str(uuid.uuid4())

    jobs[job_id] = {
        "job_id": job_id,
        "status": "started",
        "maps_url": request.maps_url,
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
# Entrypoint
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    print(f"[Site Builder] Starting on {HOST}:{PORT}")
    uvicorn.run(app, host=HOST, port=PORT)
