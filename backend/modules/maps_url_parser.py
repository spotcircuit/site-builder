"""
Google Maps URL parser -- extracts place_id, CID, coordinates, and business name
from any Google Maps URL format.

Supported URL formats:
  - https://www.google.com/maps/place/Business+Name/@lat,lng,zoom/data=...
  - https://maps.google.com/?cid=12345
  - https://goo.gl/maps/shortcode
  - https://maps.app.goo.gl/shortcode
  - https://www.google.com/maps?q=place_id:ChIJ...
  - https://www.google.com/maps/search/...
"""
import asyncio
import re
from typing import Optional
from urllib.parse import unquote, unquote_plus, urlparse, parse_qs

import httpx
from pydantic import BaseModel, Field


class ParsedMapsUrl(BaseModel):
    """Structured result from parsing a Google Maps URL."""

    place_id: Optional[str] = Field(
        default=None,
        description="Google Place ID (ChIJ format), e.g. ChIJN1t_tDeuEmsRUsoyG83frY4",
    )
    cid: Optional[str] = Field(
        default=None,
        description="Google Maps CID (numeric identifier)",
    )
    business_name: Optional[str] = Field(
        default=None,
        description="Decoded business name extracted from the URL path",
    )
    latitude: Optional[float] = Field(
        default=None,
        description="Latitude from the @lat,lng portion of the URL",
    )
    longitude: Optional[float] = Field(
        default=None,
        description="Longitude from the @lat,lng portion of the URL",
    )
    raw_url: str = Field(
        description="The original URL that was parsed (after redirect resolution)",
    )


# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

# Matches @lat,lng in a Maps URL (with optional zoom level after)
_COORDS_PATTERN = re.compile(r"@(-?\d+\.?\d*),(-?\d+\.?\d*)")

# Matches /place/Business+Name/ in a Maps URL
_PLACE_NAME_PATTERN = re.compile(r"/place/([^/@]+)")

# Matches place_id:ChIJ... in query params or URL path
_PLACE_ID_PATTERN = re.compile(r"place_id[=:]([A-Za-z0-9_-]+)")

# Matches ChIJ-style place IDs embedded in the data parameter.
# Google encodes place IDs in the !1s prefix inside the data blob.
_DATA_PLACE_ID_PATTERN = re.compile(r"!1s(0x[0-9a-fA-F]+:0x[0-9a-fA-F]+|ChIJ[A-Za-z0-9_-]+)")

# Matches ?cid=<number> or &cid=<number>
_CID_QUERY_PATTERN = re.compile(r"[?&]cid=(\d+)")

# Matches CID embedded in the data parameter (hex after 0x prefix, converted)
# Google sometimes encodes the CID as !4s or !1s0x...:0x<cid_hex>
_CID_HEX_PATTERN = re.compile(r"0x[0-9a-fA-F]+:0x([0-9a-fA-F]+)")

# Shortened URL domains that require redirect resolution
_SHORTENED_DOMAINS = {"goo.gl", "maps.app.goo.gl"}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _is_shortened_url(url: str) -> bool:
    """Return True if the URL is a Google Maps shortened link."""
    try:
        parsed = urlparse(url)
        return parsed.hostname in _SHORTENED_DOMAINS
    except Exception:
        return False


async def _resolve_redirects(url: str) -> str:
    """Follow redirects on a shortened URL and return the final destination.

    Uses httpx with redirect following enabled.  Falls back to the original
    URL if resolution fails (network error, timeout, etc.).
    """
    try:
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=httpx.Timeout(15.0, connect=10.0),
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
            },
        ) as client:
            response = await client.get(url)
            return str(response.url)
    except httpx.HTTPError:
        return url
    except Exception:
        return url


def _extract_place_id(url: str) -> Optional[str]:
    """Extract a Google Place ID from the URL.

    Place IDs appear in several positions:
      1. As a query parameter: ?q=place_id:ChIJ...
      2. Inside the data blob: /data=!...!1sChIJ...
      3. As a path segment after /place/ in some newer formats
    """
    # Check query-style place_id first
    match = _PLACE_ID_PATTERN.search(url)
    if match:
        return match.group(1)

    # Check the data parameter for an encoded place ID
    match = _DATA_PLACE_ID_PATTERN.search(url)
    if match:
        value = match.group(1)
        # If it starts with ChIJ it is already a standard place ID
        if value.startswith("ChIJ"):
            return value
        # Otherwise it is a hex-encoded reference -- return as-is since
        # Google accepts both formats for lookups
        return value

    return None


def _extract_cid(url: str) -> Optional[str]:
    """Extract a CID (numeric customer/place ID) from the URL.

    CIDs appear as:
      1. ?cid=<number> query parameter
      2. Hex-encoded in the data blob as 0x...:0x<hex_cid>
    """
    # Direct cid query parameter
    match = _CID_QUERY_PATTERN.search(url)
    if match:
        return match.group(1)

    # Parse query string for cid parameter (handles url-encoded variants)
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    if "cid" in qs:
        return qs["cid"][0]

    # Extract from hex-encoded data blob and convert to decimal CID.
    # Prefer CIDs from the !1s segment (the actual place identifier)
    # over other hex pairs like !5s (which are different data).
    import re as _re
    _1s_cid = _re.search(r"!1s(0x[0-9a-fA-F]+:0x([0-9a-fA-F]+))", url)
    if _1s_cid:
        try:
            cid_decimal = str(int(_1s_cid.group(2), 16))
            return cid_decimal
        except ValueError:
            pass
    # Fallback: use any hex pair
    match = _CID_HEX_PATTERN.search(url)
    if match:
        try:
            cid_decimal = str(int(match.group(1), 16))
            return cid_decimal
        except ValueError:
            pass

    return None


def _extract_coordinates(url: str) -> tuple[Optional[float], Optional[float]]:
    """Extract latitude and longitude from the @lat,lng portion of the URL."""
    match = _COORDS_PATTERN.search(url)
    if match:
        try:
            lat = float(match.group(1))
            lng = float(match.group(2))
            # Basic sanity check on coordinate ranges
            if -90 <= lat <= 90 and -180 <= lng <= 180:
                return lat, lng
        except ValueError:
            pass
    return None, None


def _extract_business_name(url: str) -> Optional[str]:
    """Extract and decode the business name from /place/Business+Name/ or /maps/search/query."""
    match = _PLACE_NAME_PATTERN.search(url)
    if match:
        raw_name = match.group(1)
        decoded = unquote_plus(raw_name)
        decoded = decoded.strip()
        if decoded:
            return decoded
    # Also try /maps/search/ URLs (from Places Autocomplete)
    search_match = re.search(r"/maps/search/([^?#]+)", url)
    if search_match:
        decoded = unquote_plus(search_match.group(1))
        decoded = decoded.strip()
        if decoded:
            return decoded
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def parse_maps_url(url: str) -> ParsedMapsUrl:
    """Parse any Google Maps URL into structured components.

    For shortened URLs (goo.gl / maps.app.goo.gl), the function follows
    redirects to obtain the full URL before parsing.

    Args:
        url: Any Google Maps URL (full, shortened, or with embedded data).

    Returns:
        ParsedMapsUrl with whatever fields could be extracted.

    Raises:
        ValueError: If the URL is empty or clearly not a Google Maps link.
    """
    if not url or not url.strip():
        raise ValueError("URL must not be empty")

    url = url.strip()

    # Resolve shortened URLs to their full form
    resolved_url = url
    if _is_shortened_url(url):
        resolved_url = await _resolve_redirects(url)

    # Decode any percent-encoded characters in the full URL for easier parsing
    decoded_url = unquote(resolved_url)

    # Extract all available components
    place_id = _extract_place_id(decoded_url)
    cid = _extract_cid(decoded_url)
    latitude, longitude = _extract_coordinates(decoded_url)
    business_name = _extract_business_name(decoded_url)

    return ParsedMapsUrl(
        place_id=place_id,
        cid=cid,
        business_name=business_name,
        latitude=latitude,
        longitude=longitude,
        raw_url=resolved_url,
    )


def parse_maps_url_sync(url: str) -> ParsedMapsUrl:
    """Synchronous wrapper around :func:`parse_maps_url`.

    Creates a new event loop if none is running, otherwise schedules
    the coroutine on the existing loop.

    Args:
        url: Any Google Maps URL.

    Returns:
        ParsedMapsUrl with whatever fields could be extracted.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # We are inside an async context (e.g. Jupyter, nested call).
        # Use a new thread to avoid blocking the running loop.
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(asyncio.run, parse_maps_url(url))
            return future.result(timeout=30)
    else:
        return asyncio.run(parse_maps_url(url))
