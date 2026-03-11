"""
React Site Builder Module

Assembles a complete Vite + React + TailwindCSS project from templates,
populates it with Claude-generated content, and builds static HTML output.

The template lives in backend/templates/react/ and contains all React
components. The only file that changes per generation is src/data.json
(content + business data) plus a few placeholder substitutions in config files.
"""

import asyncio
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Callable, Coroutine, Optional

from pydantic import BaseModel

ProgressCallback = Optional[Callable[[str], Coroutine[Any, Any, None]]]

TEMPLATE_DIR = Path(__file__).parent.parent / "templates" / "react"


def _inline_assets(dist_path: Path, index_html_path: Path) -> str:
    """Inline JS and CSS assets into the HTML for self-contained preview.

    Replaces <script src="/assets/..."> and <link href="/assets/...">
    tags with inline <script> and <style> blocks so the HTML works
    standalone in an iframe srcdoc.
    """
    import re

    html = index_html_path.read_text(encoding="utf-8")

    # Inline CSS: <link rel="stylesheet" ... href="/assets/xxx.css">
    def replace_css(match: re.Match) -> str:
        href = match.group(1)
        css_path = dist_path / href.lstrip("/")
        if css_path.exists():
            css_content = css_path.read_text(encoding="utf-8")
            return f"<style>{css_content}</style>"
        return match.group(0)

    html = re.sub(
        r'<link[^>]*href="(/assets/[^"]+\.css)"[^>]*/?>',
        replace_css,
        html,
    )

    # Inline JS: <script ... src="/assets/xxx.js">
    def replace_js(match: re.Match) -> str:
        src = match.group(1)
        js_path = dist_path / src.lstrip("/")
        if js_path.exists():
            js_content = js_path.read_text(encoding="utf-8")
            return f"<script type=\"module\">{js_content}</script>"
        return match.group(0)

    html = re.sub(
        r'<script[^>]*src="(/assets/[^"]+\.js)"[^>]*></script>',
        replace_js,
        html,
    )

    return html


class ReactBuildResult(BaseModel):
    """Result of assembling and building a React site."""

    dist_path: str
    build_dir: str
    index_html: str  # Content of dist/index.html for preview


def _html_escape_attr(value: str) -> str:
    """Escape a string for safe use inside an HTML attribute value."""
    return (
        value.replace("&", "&amp;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _build_favicon_data_uri(letter: str, color: str) -> str:
    """Build a base64-encoded SVG favicon data URI (safe for HTML attributes)."""
    import base64

    # Sanitize: only use alphanumeric first letter, fallback to "B"
    safe_letter = letter if letter.isalnum() else "B"
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
        f'<circle cx="50" cy="50" r="50" fill="{color}"/>'
        f'<text x="50" y="50" text-anchor="middle" dy=".35em" '
        f'font-size="50" font-weight="bold" fill="white">{safe_letter}</text>'
        f'</svg>'
    )
    encoded = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


def _substitute_placeholders(build_dir: Path, content: dict, business_data: dict) -> None:
    """Replace {{PLACEHOLDER}} tokens in template config files."""
    color_primary = content.get("color_primary", "#2563EB")
    favicon_letter = business_data.get("name", "B")[0].upper()

    replacements = {
        "{{SEO_TITLE}}": _html_escape_attr(content.get("seo_title", "Business Website")),
        "{{SEO_DESCRIPTION}}": _html_escape_attr(content.get("seo_description", "Professional business website")),
        "{{OG_TITLE}}": _html_escape_attr(content.get("og_title", content.get("seo_title", "Business Website"))),
        "{{OG_DESCRIPTION}}": _html_escape_attr(content.get("og_description", content.get("seo_description", ""))),
        "{{OG_IMAGE}}": _html_escape_attr(content.get("og_image", "")),
        "{{CANONICAL_URL}}": _html_escape_attr(content.get("canonical_url", "")),
        "{{COLOR_PRIMARY}}": color_primary,
        "{{COLOR_SECONDARY}}": content.get("color_secondary", "#F59E0B"),
        "{{FONT_HEADING}}": content.get("font_heading", "Inter"),
        "{{FONT_BODY}}": content.get("font_body", "Inter"),
        "{{FAVICON_DATA_URI}}": _build_favicon_data_uri(favicon_letter, color_primary),
    }

    # URL-encoded font names for Google Fonts link in index.html
    font_url_replacements = {
        "{{FONT_HEADING}}": content.get("font_heading", "Inter").replace(" ", "+"),
        "{{FONT_BODY}}": content.get("font_body", "Inter").replace(" ", "+"),
    }

    # Files that contain placeholders
    template_files = [
        "index.html",
        "tailwind.config.js",
    ]

    for filename in template_files:
        filepath = build_dir / filename
        if not filepath.exists():
            continue

        text = filepath.read_text(encoding="utf-8")

        # For index.html, apply URL-encoded font names first (overrides the raw ones)
        if filename == "index.html":
            for placeholder, value in font_url_replacements.items():
                text = text.replace(placeholder, str(value))

        for placeholder, value in replacements.items():
            text = text.replace(placeholder, str(value))
        filepath.write_text(text, encoding="utf-8")


def _generate_data_json(
    content: dict,
    business_data: dict,
    generated_images: Optional[dict] = None,
) -> dict:
    """Build the data.json payload that React components consume."""
    data = {
        # AI-generated content
        **content,
        # Business data for contact/map sections
        "business_name": business_data.get("name", ""),
        "phone": business_data.get("phone") or "",
        "email": business_data.get("email") or "",
        "address": business_data.get("address") or "",
        "website": business_data.get("website") or "",
        "hours": business_data.get("hours"),
        "photos": business_data.get("photos") or [],
        "latitude": business_data.get("latitude"),
        "longitude": business_data.get("longitude"),
        "rating": business_data.get("rating"),
        "review_count": business_data.get("review_count"),
        "category": business_data.get("category") or "",
        "reviews": business_data.get("reviews") or [],
    }

    # Inject website-scraped images and branding into data.json
    website_data = business_data.get("website_data")
    if website_data and isinstance(website_data, dict):
        # Logo from business website
        if website_data.get("logo_url"):
            data["website_logo_url"] = website_data["logo_url"]
        # Hero image from business website
        if website_data.get("hero_image_url"):
            data["website_hero_image"] = website_data["hero_image_url"]
        # Gallery images from business website (external URLs)
        site_images = website_data.get("images") or []
        if site_images:
            data["website_images"] = site_images[:12]
        # Brand colors from website
        if website_data.get("brand_colors"):
            data["website_brand_colors"] = website_data["brand_colors"]
        # Social links from website
        if website_data.get("social_links"):
            data["social_links"] = website_data["social_links"]

    # Use real Google reviews as testimonials if available (priority over AI-generated)
    # Only include 4-5 star reviews to present the business positively
    real_reviews = business_data.get("reviews") or []
    if real_reviews:
        data["testimonials"] = [
            {
                "author": r.get("author", "Customer"),
                "rating": r.get("rating", 5),
                "text": r.get("text", ""),
                "time": r.get("time", ""),
                "verified": True,
            }
            for r in real_reviews
            if r.get("text") and (r.get("rating") or 5) >= 4
        ]

    # Inject AI-generated image paths
    if generated_images:
        if generated_images.get("hero_image"):
            data["ai_hero_image"] = f"/images/{generated_images['hero_image']}"
        if generated_images.get("about_image"):
            data["ai_about_image"] = f"/images/{generated_images['about_image']}"
        if generated_images.get("gallery_images"):
            data["ai_gallery_images"] = [
                f"/images/{img}" for img in generated_images["gallery_images"]
            ]
        if generated_images.get("services_image"):
            data["ai_services_image"] = f"/images/{generated_images['services_image']}"
        if generated_images.get("why_choose_us_image"):
            data["ai_why_choose_us_image"] = f"/images/{generated_images['why_choose_us_image']}"
        if generated_images.get("contact_image"):
            data["ai_contact_image"] = f"/images/{generated_images['contact_image']}"

    return data


async def _run_command(cmd: list[str], cwd: Path, timeout: int = 180) -> str:
    """Run a shell command asynchronously and return stdout."""
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        cwd=str(cwd),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)

    if proc.returncode != 0:
        error_msg = stderr.decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Command {' '.join(cmd)} failed (exit {proc.returncode}): {error_msg}"
        )

    return stdout.decode("utf-8", errors="replace")


async def build_react_site(
    content: dict,
    business_data: dict,
    job_id: str,
    callback: ProgressCallback = None,
    generated_images: Optional[dict] = None,
) -> ReactBuildResult:
    """Assemble and build a React site from templates.

    Steps:
        1. Copy template directory to a temp build location
        2. Generate src/data.json from content + business data
        3. Substitute placeholders in config files
        4. Run npm install (cached) + npm run build
        5. Return the dist/ path and index.html content

    Args:
        content: SiteContent model dumped as dict
        business_data: Scraped business data dict
        job_id: Unique job identifier
        callback: Optional progress callback

    Returns:
        ReactBuildResult with paths and preview HTML
    """
    import tempfile

    build_dir = Path(tempfile.mkdtemp(prefix=f"site_build_{job_id[:8]}_"))

    try:
        # Step 1: Copy template
        if callback:
            await callback("Copying React template files...")

        if build_dir.exists():
            shutil.rmtree(build_dir)

        def _ignore_build_artifacts(directory: str, contents: list[str]) -> list[str]:
            """Skip node_modules and dist when copying template."""
            return [c for c in contents if c in ("node_modules", "dist")]

        shutil.copytree(TEMPLATE_DIR, build_dir, ignore=_ignore_build_artifacts)

        # Step 2: Generate data.json
        if callback:
            await callback("Generating site data from AI content...")

        # Copy AI-generated images into public/images/ if available
        if generated_images and generated_images.get("image_dir"):
            if callback:
                await callback("Copying AI-generated images...")
            image_src = Path(generated_images["image_dir"])
            image_dst = build_dir / "public" / "images"
            image_dst.mkdir(parents=True, exist_ok=True)
            for img_file in image_src.iterdir():
                if img_file.is_file():
                    shutil.copy2(img_file, image_dst / img_file.name)

        data_payload = _generate_data_json(content, business_data, generated_images)
        data_json_path = build_dir / "src" / "data.json"
        data_json_path.write_text(
            json.dumps(data_payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        # Step 3: Substitute placeholders
        if callback:
            await callback("Configuring project settings...")

        _substitute_placeholders(build_dir, content, business_data)

        # Step 4: Install dependencies
        # Use the template's own node_modules if they exist (from initial setup),
        # otherwise run npm install. We use cp -a to preserve symlinks in .bin/
        if callback:
            await callback("Installing dependencies...")

        template_node_modules = TEMPLATE_DIR / "node_modules"
        node_modules_dst = build_dir / "node_modules"

        if template_node_modules.exists():
            # Fast path: copy from template dir (preserves symlinks)
            if callback:
                await callback("Copying pre-installed dependencies...")
            await _run_command(
                ["cp", "-a", str(template_node_modules), str(node_modules_dst)],
                build_dir,
                timeout=60,
            )
        else:
            # Slow path: fresh install
            if callback:
                await callback("Running npm install (first time)...")
            await _run_command(["npm", "install", "--prefer-offline"], build_dir, timeout=120)

        # Step 5: Build
        if callback:
            await callback("Building React site (npm run build)...")

        await _run_command(["npm", "run", "build"], build_dir, timeout=90)

        # Read the built files and inline everything for preview
        dist_path = build_dir / "dist"
        index_html_path = dist_path / "index.html"

        if not index_html_path.exists():
            raise RuntimeError(
                f"Build succeeded but dist/index.html not found at {dist_path}"
            )

        index_html = _inline_assets(dist_path, index_html_path)

        if callback:
            await callback("React site built successfully!")

        return ReactBuildResult(
            dist_path=str(dist_path),
            build_dir=str(build_dir),
            index_html=index_html,
        )

    except Exception:
        # Don't clean up on error so we can debug
        raise


async def rebuild_react_site(
    data: dict,
    build_dir: str,
    callback: ProgressCallback = None,
) -> ReactBuildResult:
    """Re-build an existing React site with updated data.json.

    Much faster than full build_react_site() because it skips:
    - Template copy (build_dir already has everything)
    - npm install (node_modules already present)
    Only writes new data.json, re-substitutes placeholders, and re-runs npm build.

    Args:
        data: The full data.json payload (merged content + business data)
        build_dir: Path to existing build directory from initial generation
        callback: Optional progress callback

    Returns:
        ReactBuildResult with updated HTML
    """
    build_path = Path(build_dir)

    if not build_path.exists():
        raise RuntimeError(f"Build directory not found: {build_dir}")

    if callback:
        await callback("Updating site data...")

    # Write updated data.json
    data_json_path = build_path / "src" / "data.json"
    data_json_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # Re-substitute placeholders (colors/fonts may have changed)
    if callback:
        await callback("Applying design changes...")

    # Re-copy template config files first so placeholders are fresh
    for fname in ("index.html", "tailwind.config.js"):
        template_file = TEMPLATE_DIR / fname
        if template_file.exists():
            shutil.copy2(template_file, build_path / fname)

    # Build a content-like dict from data for placeholder substitution
    content_for_placeholders = {
        "seo_title": data.get("seo_title", "Business Website"),
        "seo_description": data.get("seo_description", ""),
        "og_title": data.get("og_title", data.get("seo_title", "")),
        "og_description": data.get("og_description", data.get("seo_description", "")),
        "og_image": data.get("og_image", ""),
        "canonical_url": data.get("canonical_url", ""),
        "color_primary": data.get("color_primary", "#2563EB"),
        "color_secondary": data.get("color_secondary", "#F59E0B"),
        "font_heading": data.get("font_heading", "Inter"),
        "font_body": data.get("font_body", "Inter"),
    }
    business_for_placeholders = {"name": data.get("business_name", "Business")}
    _substitute_placeholders(build_path, content_for_placeholders, business_for_placeholders)

    # Re-build
    if callback:
        await callback("Rebuilding site (npm run build)...")

    await _run_command(["npm", "run", "build"], build_path, timeout=90)

    # Inline assets for preview
    dist_path = build_path / "dist"
    index_html_path = dist_path / "index.html"

    if not index_html_path.exists():
        raise RuntimeError(f"Rebuild succeeded but dist/index.html not found")

    index_html = _inline_assets(dist_path, index_html_path)

    if callback:
        await callback("Site rebuilt successfully!")

    return ReactBuildResult(
        dist_path=str(dist_path),
        build_dir=str(build_path),
        index_html=index_html,
    )


def cleanup_build(build_dir: str) -> None:
    """Remove a temporary build directory after deployment."""
    path = Path(build_dir)
    if path.exists() and str(path).startswith("/tmp/"):
        shutil.rmtree(path, ignore_errors=True)
