"""
Cloudflare Pages Deployer Module

Deploys generated static sites to Cloudflare Pages via wrangler CLI.
Includes built-in CDN, DDoS protection, and edge caching.

Requires CLOUDFLARE_API_TOKEN and CLOUDFLARE_ACCOUNT_ID environment variables.
Uses `npx wrangler pages deploy` for reliable direct uploads.
"""

import asyncio
import logging
import os
import re
from pathlib import Path
from typing import Any, Callable, Coroutine, Optional

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

    # Step 1: Ensure project exists via Cloudflare API (faster than wrangler)
    if callback:
        await callback(f"Ensuring project '{project_name}' exists...")

    import httpx

    api_base = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/pages/projects"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            # Check if project exists
            check = await client.get(f"{api_base}/{project_name}", headers=headers)
            if check.status_code == 404 or not check.json().get("success"):
                # Create the project
                create_resp = await client.post(
                    api_base,
                    headers=headers,
                    json={
                        "name": project_name,
                        "production_branch": "main",
                    },
                )
                create_data = create_resp.json()
                if create_data.get("success"):
                    logger.info(f"Created Cloudflare Pages project: {project_name}")
                else:
                    logger.warning(f"Project create response: {create_data}")
            else:
                logger.info(f"Cloudflare Pages project '{project_name}' already exists")
    except Exception as e:
        logger.warning(f"Project ensure failed (will try deploy anyway): {e}")

    # Step 2: Deploy
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
    # Typical output: "✨ Deployment complete! Take a peek over at https://xxxxx.project-name.pages.dev"
    url = ""
    deployment_id = ""
    combined = stdout_str + "\n" + stderr_str

    # Look for deployment-specific URL in output
    # e.g. https://7005caee.joes-pizza-test.pages.dev
    url_match = re.search(r"(https://[a-z0-9.-]+\.pages\.dev)", combined)
    if url_match:
        # Wrangler returns the deployment-specific URL (with hash prefix)
        # but we want the stable production URL for the user
        deployment_url = url_match.group(1)
        logger.info(f"Deployment-specific URL: {deployment_url}")

    # Look for deployment ID
    id_match = re.search(r"Deployment ID:\s*([a-f0-9-]+)", combined)
    if id_match:
        deployment_id = id_match.group(1)

    # Always use the stable production URL (no hash prefix)
    # SSL is immediately available on this URL, unlike deployment-specific ones
    url = f"https://{project_name}.pages.dev"

    if callback:
        await callback(f"Deployed to Cloudflare Pages: {url}")

    return CloudflareDeployResult(
        deployment_id=deployment_id,
        url=url,
        project_name=project_name,
    )
