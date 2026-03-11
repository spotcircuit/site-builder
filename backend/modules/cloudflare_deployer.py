"""
Cloudflare Pages Deployer Module

Deploys generated static sites to Cloudflare Pages via wrangler CLI.
Includes built-in CDN, DDoS protection, and edge caching.

Requires CLOUDFLARE_API_TOKEN and CLOUDFLARE_ACCOUNT_ID environment variables.
Uses `npx wrangler pages deploy` for reliable direct uploads.

Automatically manages project limits by deleting the oldest project
when the account limit is reached.
"""

import asyncio
import logging
import os
import re
from pathlib import Path
from typing import Any, Callable, Coroutine, Optional

import httpx
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

ProgressCallback = Optional[Callable[[str], Coroutine[Any, Any, None]]]


class CloudflareDeployResult(BaseModel):
    """Result of a Cloudflare Pages deployment."""

    deployment_id: str = ""
    url: str
    project_name: str
    provider: str = "cloudflare"


def is_cloudflare_configured() -> bool:
    """Check if Cloudflare deployment is configured."""
    return bool(
        os.environ.get("CLOUDFLARE_API_TOKEN")
        and os.environ.get("CLOUDFLARE_ACCOUNT_ID")
    )


def _sanitize_project_name(business_name: str, job_id: str) -> str:
    """Create a valid Cloudflare Pages project name."""
    slug = business_name.lower().strip()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s]+", "-", slug)
    slug = slug[:40].strip("-")
    if not slug:
        slug = "generated-site"
    short_hash = job_id[:6] if job_id else "000000"
    return f"site-{slug}-{short_hash}"


async def _ensure_project_exists(
    project_name: str,
    token: str,
    account_id: str,
    callback: ProgressCallback = None,
) -> bool:
    """Ensure a Cloudflare Pages project exists, creating it if needed.

    If the account project limit is reached, deletes the oldest project
    to make room. Returns True if the project is ready.
    """
    api_base = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/pages/projects"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    async with httpx.AsyncClient(timeout=20) as client:
        # Check if project already exists
        check = await client.get(f"{api_base}/{project_name}", headers=headers)
        if check.status_code == 200 and check.json().get("success"):
            logger.info(f"Project '{project_name}' already exists")
            return True

        # Try to create it
        create_resp = await client.post(
            api_base,
            headers=headers,
            json={"name": project_name, "production_branch": "main"},
        )
        create_data = create_resp.json()

        if create_data.get("success"):
            logger.info(f"Created project: {project_name}")
            return True

        # Check if it's a project limit error
        errors = create_data.get("errors", [])
        is_limit = any(e.get("code") == 8000027 for e in errors)

        if not is_limit:
            logger.error(f"Failed to create project: {create_data}")
            return False

        # Hit project limit — delete the oldest project to make room
        if callback:
            await callback("Account project limit reached, removing oldest site...")

        logger.warning("Project limit reached, deleting oldest project")

        list_resp = await client.get(api_base, headers=headers)
        list_data = list_resp.json()
        projects = list_data.get("result") or []

        if not projects:
            logger.error("No projects to delete but limit reached")
            return False

        # Sort by created_on ascending (oldest first)
        projects.sort(key=lambda p: p.get("created_on", ""))
        oldest = projects[0]
        oldest_name = oldest.get("name", "")

        if callback:
            await callback(f"Deleting oldest project: {oldest_name}...")

        delete_resp = await client.delete(
            f"{api_base}/{oldest_name}", headers=headers
        )
        delete_data = delete_resp.json()

        if delete_data.get("success"):
            logger.info(f"Deleted oldest project: {oldest_name}")
        else:
            logger.error(f"Failed to delete project {oldest_name}: {delete_data}")
            return False

        # Now create again
        retry_resp = await client.post(
            api_base,
            headers=headers,
            json={"name": project_name, "production_branch": "main"},
        )
        retry_data = retry_resp.json()

        if retry_data.get("success"):
            logger.info(f"Created project after cleanup: {project_name}")
            return True

        logger.error(f"Still failed after cleanup: {retry_data}")
        return False


async def deploy_to_cloudflare(
    dist_path: Path,
    business_name: str,
    job_id: str = "",
    callback: ProgressCallback = None,
) -> CloudflareDeployResult:
    """Deploy static files to Cloudflare Pages via wrangler CLI.

    Uses `npx wrangler pages deploy <dir> --project-name=<name>` which
    handles file hashing, manifest creation, and upload reliably.

    Args:
        dist_path: Path to the built dist/ directory
        business_name: Business name for project naming
        job_id: Job ID for unique naming
        callback: Optional progress callback

    Returns:
        CloudflareDeployResult with live URL
    """
    token = (os.environ.get("CLOUDFLARE_API_TOKEN") or "").strip()
    account_id = (os.environ.get("CLOUDFLARE_ACCOUNT_ID") or "").strip()

    if not token or not account_id:
        raise ValueError(
            "CLOUDFLARE_API_TOKEN and CLOUDFLARE_ACCOUNT_ID must be set"
        )

    project_name = _sanitize_project_name(business_name, job_id)

    if callback:
        await callback(f"Deploying to Cloudflare Pages ({project_name})...")

    env = {
        **os.environ,
        "CLOUDFLARE_API_TOKEN": token,
        "CLOUDFLARE_ACCOUNT_ID": account_id,
    }

    # Step 1: Ensure project exists (auto-manages project limit)
    if callback:
        await callback(f"Ensuring project '{project_name}' exists...")

    try:
        project_ready = await _ensure_project_exists(
            project_name, token, account_id, callback
        )
        if not project_ready:
            raise RuntimeError(
                f"Could not create Cloudflare Pages project '{project_name}'"
            )
    except httpx.HTTPError as e:
        raise RuntimeError(f"Cloudflare API error: {e}")

    # Step 2: Deploy via wrangler
    cmd = [
        "npx", "wrangler", "pages", "deploy",
        str(dist_path),
        f"--project-name={project_name}",
        "--branch=main",
        "--commit-dirty=true",
    ]

    if callback:
        await callback("Running wrangler pages deploy...")

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env,
    )

    stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)
    stdout_str = stdout.decode("utf-8", errors="replace")
    stderr_str = stderr.decode("utf-8", errors="replace")

    logger.info(f"Wrangler stdout: {stdout_str}")
    if stderr_str:
        logger.info(f"Wrangler stderr: {stderr_str}")

    if proc.returncode != 0:
        raise RuntimeError(
            f"wrangler pages deploy failed (exit {proc.returncode}): {stderr_str or stdout_str}"
        )

    # Extract URL from wrangler output
    url = ""
    deployment_id = ""
    combined = stdout_str + "\n" + stderr_str

    url_match = re.search(r"(https://[a-z0-9.-]+\.pages\.dev)", combined)
    if url_match:
        deployment_url = url_match.group(1)
        logger.info(f"Deployment-specific URL: {deployment_url}")

    id_match = re.search(r"Deployment ID:\s*([a-f0-9-]+)", combined)
    if id_match:
        deployment_id = id_match.group(1)

    # Stable production URL
    url = f"https://{project_name}.pages.dev"

    if callback:
        await callback(f"Deployed to Cloudflare Pages: {url}")

    return CloudflareDeployResult(
        deployment_id=deployment_id,
        url=url,
        project_name=project_name,
    )
