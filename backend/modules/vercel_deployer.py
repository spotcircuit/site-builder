"""
Vercel Deployer Module

Deploys generated static sites to Vercel via their REST API.
Returns a live URL for the deployed site.

Requires VERCEL_TOKEN environment variable.
Optionally uses VERCEL_TEAM_ID for team deployments.
"""

import base64
import hashlib
import os
from pathlib import Path
from typing import Any, Callable, Coroutine, Optional

import httpx
from pydantic import BaseModel, Field

ProgressCallback = Optional[Callable[[str], Coroutine[Any, Any, None]]]

VERCEL_API_BASE = "https://api.vercel.com"


class VercelDeployResult(BaseModel):
    """Result of a Vercel deployment."""
    deployment_id: str
    url: str
    project_name: str
    provider: str = "vercel"


def is_vercel_configured() -> bool:
    """Check if Vercel deployment is configured."""
    return bool(os.environ.get("VERCEL_TOKEN"))


def _sanitize_project_name(business_name: str, job_id: str) -> str:
    """Create a valid Vercel project name from business name."""
    import re
    slug = business_name.lower().strip()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s]+', '-', slug)
    slug = slug[:40].strip('-')
    if not slug:
        slug = "generated-site"
    # Append short hash from job_id to avoid collisions
    short_hash = job_id[:6] if job_id else "000000"
    return f"site-{slug}-{short_hash}"


def _collect_files(dist_path: Path) -> list[dict]:
    """Walk dist/ and collect all files as {file, data} dicts for Vercel API.

    Vercel v13 deployments API accepts files with:
    - "file": relative path
    - "data": file content as string (for text) or base64

    For simplicity, we base64 encode everything.
    """
    files = []
    for file_path in dist_path.rglob("*"):
        if file_path.is_file():
            relative = str(file_path.relative_to(dist_path))
            content = file_path.read_bytes()
            # Vercel accepts "data" as base64 string with encoding specified
            files.append({
                "file": relative,
                "data": base64.b64encode(content).decode("ascii"),
                "encoding": "base64",
            })
    return files


async def deploy_to_vercel(
    dist_path: Path,
    business_name: str,
    job_id: str = "",
    callback: ProgressCallback = None,
) -> VercelDeployResult:
    """Deploy static files from dist/ to Vercel.

    Args:
        dist_path: Path to the built dist/ directory
        business_name: Business name for project naming
        job_id: Job ID for unique project naming
        callback: Optional progress callback

    Returns:
        VercelDeployResult with live URL

    Raises:
        ValueError: If VERCEL_TOKEN is not set
        httpx.HTTPStatusError: If Vercel API returns an error
    """
    token = os.environ.get("VERCEL_TOKEN")
    if not token:
        raise ValueError("VERCEL_TOKEN environment variable is not set")

    team_id = os.environ.get("VERCEL_TEAM_ID")
    project_name = _sanitize_project_name(business_name, job_id)

    if callback:
        await callback(f"Preparing files for Vercel deployment...")

    files = _collect_files(dist_path)

    if callback:
        await callback(f"Uploading {len(files)} files to Vercel...")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    params = {}
    if team_id:
        params["teamId"] = team_id

    payload = {
        "name": project_name,
        "files": files,
        "projectSettings": {
            "framework": None,
            "buildCommand": "",
            "outputDirectory": ".",
        },
        "target": "production",
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        if callback:
            await callback("Creating Vercel deployment...")

        response = await client.post(
            f"{VERCEL_API_BASE}/v13/deployments",
            headers=headers,
            params=params,
            json=payload,
        )
        response.raise_for_status()

        result = response.json()

        deployment_id = result.get("id", "")
        # The URL returned by Vercel doesn't include protocol
        raw_url = result.get("url", "")
        url = f"https://{raw_url}" if raw_url and not raw_url.startswith("http") else raw_url

        if callback:
            await callback(f"Deployed to Vercel: {url}")

        return VercelDeployResult(
            deployment_id=deployment_id,
            url=url,
            project_name=project_name,
        )
