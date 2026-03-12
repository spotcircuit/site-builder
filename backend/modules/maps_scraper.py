"""
Google Maps Business Scraper

Scrapes a single business from Google Maps using Playwright.
Extracts all data needed to generate a website: profile info, photos, reviews,
hours, services, and location coordinates.

Selectors ported from the getrankedlocal production scrapers which are
confirmed working as of 2025.
"""

import asyncio
import logging
from typing import Any, Callable, Coroutine, Optional

from pydantic import BaseModel, Field
from playwright.async_api import async_playwright, Page, Browser

logger = logging.getLogger(__name__)

# Type alias for the optional progress callback
ProgressCallback = Optional[Callable[[dict[str, str]], Coroutine[Any, Any, None]]]


class BusinessData(BaseModel):
    """Complete business data extracted from Google Maps."""

    name: str
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    category: Optional[str] = None
    hours: Optional[dict[str, str]] = Field(default=None, description="Day -> hours string mapping")
    hours_raw: Optional[str] = Field(default=None, description="Raw hours aria-label string")
    services: Optional[list[str]] = None
    photos: Optional[list[str]] = Field(default=None, description="Photo URLs from the business listing")
    reviews: Optional[list[dict[str, Any]]] = Field(
        default=None,
        description="List of review dicts with keys: author, rating, text, time",
    )
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    place_id: Optional[str] = None
    cid: Optional[str] = None
    open_now: Optional[bool] = None
    status_text: Optional[str] = None
    description: Optional[str] = Field(default=None, description="Short business description from Google Maps overview")
    photo_count: Optional[int] = Field(default=None, description="Total photos available on Google Maps")
    review_topics: Optional[dict[str, int]] = Field(default=None, description="Topics mentioned in reviews with counts")
    price_info: Optional[str] = None
    has_menu: Optional[bool] = None
    links: Optional[dict[str, str]] = Field(default=None, description="Appointment, order, menu links")


# ---------------------------------------------------------------------------
# JavaScript to extract business profile - uses proven getrankedlocal selectors
# ---------------------------------------------------------------------------
EXTRACT_PROFILE_JS = """() => {
    const data = {};

    // Name - h1 with aria-label (most reliable), then plain h1 fallback
    const nameElem = document.querySelector('h1[aria-label]') || document.querySelector('h1.DUwDvf') || document.querySelector('h1');
    if (nameElem) data.name = nameElem.innerText.trim();

    // Address - data-item-id="address"
    const addressElem = document.querySelector('[data-item-id="address"]');
    if (addressElem) {
        data.address = addressElem.innerText
            .replace(/\\n/g, ', ')
            .replace(/[\\u0000-\\u001F\\u007F-\\uFFFF]/g, '')
            .replace(/^[,\\s]+/, '')  // Remove leading commas/spaces
            .trim();
    }

    // Phone - extracted from data-item-id attribute itself (most reliable)
    const phoneElem = document.querySelector('[data-item-id^="phone:tel:"]');
    if (phoneElem) {
        const phoneAttr = phoneElem.getAttribute('data-item-id');
        data.phone = phoneAttr.replace('phone:tel:', '');
    }

    // Website
    const websiteElem = document.querySelector('[data-item-id="authority"]');
    if (websiteElem) {
        // Try href first, then innerText
        const href = websiteElem.getAttribute('href') || '';
        if (href && href.startsWith('http')) {
            data.website = href;
        } else {
            data.website = websiteElem.innerText.trim()
                .replace(/[\\u0000-\\u001F\\u007F-\\uFFFF]/g, '')
                .trim();
        }
    }

    // Rating - prefer role="img" elements with numeric star labels
    try {
        const ratingEls = document.querySelectorAll(
            '[role="img"][aria-label*="stars"], [aria-label*="stars"], div[aria-label*="Rated"]'
        );
        for (const el of ratingEls) {
            const r = (el.getAttribute('aria-label') || '').trim();
            const m = r.match(/([0-9]+(?:\\.[0-9]+)?)\\s*stars?/i);
            if (m) {
                data.rating = parseFloat(m[1]);
                break;
            }
        }
    } catch {}

    // Review count - broad search for "N reviews" pattern
    // Also try aria-labels like "4.3 stars 523 reviews"
    try {
        // Method 1: from aria-label that contains both stars and reviews
        const starReviewEls = document.querySelectorAll('[aria-label*="review"]');
        for (const el of starReviewEls) {
            const label = el.getAttribute('aria-label') || '';
            const m = label.match(/([\d,]+)\s+reviews?/i);
            if (m) {
                data.review_count = parseInt(m[1].replace(/,/g, ''), 10);
                break;
            }
        }
        // Method 2: from text content
        if (!data.review_count) {
            const candidates = Array.from(document.querySelectorAll('button, a, span, div'));
            const revEl = candidates.find(el =>
                (el.textContent || '').match(/\\b[\\d,]+\\s+reviews?\\b/i)
            );
            if (revEl) {
                const txt = revEl.textContent || '';
                const m = txt.match(/\\b([\\d,]+)\\s+reviews?\\b/i);
                if (m) data.review_count = parseInt(m[1].replace(/,/g, ''), 10);
            }
        }
    } catch {}

    // Category - try specific selectors for the category button in the header area
    let categoryText = '';
    const catElem = document.querySelector('button.DkEaL') ||
                    document.querySelector('button[jsaction*="pane.rating.category"]') ||
                    document.querySelector('[data-value="category"]');
    if (catElem) {
        categoryText = catElem.innerText || '';
    }
    if (!categoryText) {
        // Fallback: look in the header/info area only (not the whole page)
        // The category appears near the rating stars, inside the main info panel
        const headerArea = document.querySelector('div[role="main"] div.fontBodyMedium') ||
                           document.querySelector('div[role="main"]');
        if (headerArea) {
            const candidates = headerArea.querySelectorAll('button, span');
            for (const el of candidates) {
                const t = (el.innerText || '').trim();
                // Category is typically a short single-line text near the top
                if (t && t.length > 3 && t.length < 50 &&
                    !t.includes('\\n') &&
                    !t.includes('star') && !t.includes('review') &&
                    !t.includes('Directions') && !t.includes('Save') &&
                    !t.includes('Send') && !t.includes('Share') &&
                    !t.includes('Sponsored') && !t.includes('Ad') &&
                    !t.includes('Open') && !t.includes('Close') &&
                    !t.includes('hour') && !t.includes('mile') &&
                    !/^[\\d.,]+$/.test(t)) {
                    // Check if it looks like a category (contains a middle dot or known suffix)
                    if (t.includes('·') || t.includes('\\u00b7') ||
                        /\\b(restaurant|bar|hotel|spa|shop|store|salon|clinic|hospital|gym|studio|cafe|bakery|agency|school|church|museum|theater|theatre|pharmacy|dentist|doctor|lawyer|plumber|electrician)\\b/i.test(t)) {
                        categoryText = t;
                        break;
                    }
                }
            }
        }
    }
    if (categoryText) {
        // Split on any middle dot variant and take the first part
        const clean = categoryText.split(/[·\\u00b7\\u2022\\u2027]/)[0].trim();
        if (clean && clean.length > 2) {
            data.category = clean;
        }
    }

    // Business description (the short blurb on the overview)
    try {
        // Look for the description text - usually a div/span with a sentence about the business
        const descCandidates = document.querySelectorAll('div, span');
        for (const el of descCandidates) {
            const t = (el.innerText || '').trim();
            // Description is typically 30-300 chars, contains periods, and isn't an address
            if (t.length > 30 && t.length < 300 && t.includes('.') &&
                !t.includes('\\n') && !t.includes('Directions') &&
                !t.includes('Save') && !t.includes('Share') &&
                !t.includes('stars') && !t.includes('review')) {
                data.description = t;
                break;
            }
        }
    } catch {}

    // Hours - Method 1: individual day buttons (most reliable, from production code)
    const hours = {};
    try {
        const hoursButtons = document.querySelectorAll(
            'button[aria-label*="day,"][aria-label*="AM"], ' +
            'button[aria-label*="day,"][aria-label*="PM"], ' +
            'button[aria-label*="day,"][aria-label*="Closed"]'
        );
        hoursButtons.forEach(btn => {
            const label = btn.getAttribute('aria-label');
            if (label) {
                const match = label.match(/^(\\w+day),\\s*(.+?)(?:,\\s*Copy)?$/);
                if (match) {
                    let hoursText = match[2]
                        .replace(/, Copy open hours/g, '')
                        .replace(/[\\u202f]/g, ' ')
                        .trim();
                    hours[match[1]] = hoursText;
                }
            }
        });
    } catch {}

    // Hours - Method 2: table rows (fallback)
    if (Object.keys(hours).length === 0) {
        const hourRows = document.querySelectorAll(
            'table.eK4R0e tr, table.WgFkxc tr, table.y0skZc tr, ' +
            'div[aria-label*="hour"] table tr'
        );
        for (const row of hourRows) {
            const cells = row.querySelectorAll('td');
            if (cells.length >= 2) {
                const day = cells[0].innerText.trim();
                const time = cells[1].innerText.trim();
                if (day && time) hours[day] = time;
            }
        }
    }
    if (Object.keys(hours).length > 0) data.hours = hours;

    // Hours - Method 3: raw aria-label string (last resort, parsed in Python)
    if (Object.keys(hours).length === 0) {
        const hoursElem = document.querySelector('[aria-label*="Hours"]');
        if (hoursElem) {
            data.hours_raw = hoursElem.getAttribute('aria-label');
        }
    }

    // Photo count (so we know how many are available)
    try {
        const photoButtons = document.querySelectorAll('[aria-label*="Photos"], [aria-label*="photos"]');
        photoButtons.forEach(btn => {
            const label = btn.getAttribute('aria-label');
            if (label) {
                const match = label.match(/(\\d+)\\s+photos?/);
                if (match) data.photo_count = parseInt(match[1]);
            }
        });
    } catch {}

    // Review topics (what people mention most)
    try {
        const topicButtons = document.querySelectorAll(
            'button[aria-label*="mentioned in"][aria-label*="reviews"]'
        );
        if (topicButtons.length > 0) {
            const topics = {};
            topicButtons.forEach(btn => {
                const label = btn.getAttribute('aria-label');
                if (label) {
                    const match = label.match(/([^,]+),\\s*mentioned in\\s*(\\d+)\\s*reviews?/);
                    if (match) topics[match[1].trim()] = parseInt(match[2]);
                }
            });
            if (Object.keys(topics).length > 0) data.review_topics = topics;
        }
    } catch {}

    // Services/amenities - filter out non-service icons
    try {
        const skipPatterns = /stars?|hours|open|show|photo|review|rating|price/i;
        const chipEls = Array.from(document.querySelectorAll(
            '[role="img"][aria-label*="Has"], ' +
            '[role="img"][aria-label*="accessible"], ' +
            '[role="img"][aria-label*="Wheelchair"], ' +
            'button[aria-label*="Has"], button[aria-label*="Offers"]'
        ));
        const serviceSet = new Set();
        for (const el of chipEls) {
            let label = (el.getAttribute('aria-label') || '').trim();
            if (!label || skipPatterns.test(label)) continue;
            label = label.replace(/^(Has|Offers)\\s+/i, '');
            if (label.length > 2 && label.length < 80) serviceSet.add(label);
        }
        const services = Array.from(serviceSet);
        if (services.length > 0) data.services = services;
    } catch {}

    // Open/Closed status - find the smallest element with Open/Closed text
    try {
        const statusCandidates = Array.from(document.querySelectorAll('span, div'));
        let bestEl = null;
        let bestLen = Infinity;
        for (const el of statusCandidates) {
            const t = (el.innerText || '').trim();
            if (t.length < 80 && t.length < bestLen &&
                /\\b(Open|Closed|Closes|Opens)\\b/i.test(t) &&
                (t.includes('·') || t.includes('Closes') || t.includes('Opens') || t === 'Open' || t === 'Closed')) {
                bestEl = el;
                bestLen = t.length;
            }
        }
        if (bestEl) {
            const s = bestEl.innerText.trim();
            data.status_text = s;
            data.open_now = /\\bOpen\\b/i.test(s) && !/\\bClosed\\b/i.test(s);
        }
    } catch {}

    // Price level
    const priceElem = document.querySelector('[aria-label*="Price"]');
    if (priceElem) {
        data.price_info = priceElem.getAttribute('aria-label');
    }

    // Menu link
    const menuElem = document.querySelector('[data-item-id="menu"]');
    if (menuElem) data.has_menu = true;

    // Appointment / Order / Reserve links
    try {
        const linkCandidates = Array.from(document.querySelectorAll('a[aria-label], a[data-item-id]'));
        const links = {};
        for (const a of linkCandidates) {
            const label = (a.getAttribute('aria-label') || a.getAttribute('data-item-id') || '').toLowerCase();
            const href = a.getAttribute('href') || '';
            if (!href) continue;
            if (label.includes('appointment') || label.includes('reserve')) links.appointment = href;
            if (label.includes('order')) links.order = href;
            if (label.includes('menu')) links.menu = href;
        }
        if (Object.keys(links).length) data.links = links;
    } catch {}

    // Coordinates from URL
    const currentUrl = window.location.href;
    try {
        const coordMatch = currentUrl.match(/@(-?\\d+\\.\\d+),(-?\\d+\\.\\d+)/);
        if (coordMatch) {
            data.latitude = parseFloat(coordMatch[1]);
            data.longitude = parseFloat(coordMatch[2]);
        }
    } catch {}

    // CID from URL
    const cidMatch = currentUrl.match(/[?&]cid=([^&]+)/);
    if (cidMatch) data.cid = cidMatch[1];

    return data;
}"""

# ---------------------------------------------------------------------------
# JavaScript to extract reviews from the Reviews tab
# Uses .MyEned / .wiI7pd classes for the actual review body text.
# Deduplicates by data-review-id.
# ---------------------------------------------------------------------------
EXTRACT_REVIEWS_JS = """(maxReviews) => {
    const reviews = [];
    const seen = new Set();
    const containers = document.querySelectorAll("[data-review-id]");

    containers.forEach(container => {
        if (reviews.length >= maxReviews) return;

        const rid = container.getAttribute("data-review-id");
        if (seen.has(rid)) return;
        seen.add(rid);

        const review = {};

        // Author — .d4r55 or first link inside .WNxzHc
        const authorEl = container.querySelector(".d4r55, .WNxzHc a");
        if (authorEl) review.author = authorEl.innerText.trim();

        // Star rating from aria-label
        const ratingEl = container.querySelector('[role="img"][aria-label*="star"]');
        if (ratingEl) {
            const m = ratingEl.getAttribute("aria-label").match(/(\\d)/);
            if (m) review.rating = parseInt(m[1]);
        }

        // Time (e.g. "3 months ago")
        const timeEl = container.querySelector(".rsqaWe");
        if (timeEl) review.time = timeEl.innerText.trim();

        // ── Actual review text ──
        // Google wraps the written review in .MyEned or .wiI7pd
        const textEl = container.querySelector(".wiI7pd, .MyEned");
        if (textEl) {
            let txt = textEl.innerText.trim();
            // Strip trailing structured metadata that sometimes leaks in
            const metaCut = txt.search(/\\n(Meal type|Price per person|Food:|Service:|Atmosphere:|Noise level|Group size|Parking|Recommended|Vegetarian)/);
            if (metaCut > 0) txt = txt.substring(0, metaCut).trim();
            review.text = txt;
        }

        // Fallback: find the longest natural-language span/div
        // (skip structured metadata like "Meal type", "Food:", etc.)
        if (!review.text) {
            let best = "";
            container.querySelectorAll("span, div").forEach(el => {
                const t = (el.innerText || "").trim();
                if (t.length < 40) return;
                // Skip structured review metadata
                if (/Meal type|Food:|Price per|Atmosphere:|Parking|Noise level|Recommended|Service:|Vegetarian|Group size/i.test(t)) return;
                const colonCount = (t.match(/:/g) || []).length;
                const wordCount = t.split(" ").length;
                if (wordCount > 5 && colonCount < 3 && t.length > best.length) {
                    best = t;
                }
            });
            if (best) review.text = best;
        }

        // Helpful count
        const helpfulEl = container.querySelector("[aria-label*=Helpful]");
        if (helpfulEl) {
            const hm = helpfulEl.getAttribute("aria-label").match(/(\\d+)/);
            if (hm) review.helpful = parseInt(hm[1]);
        }

        // Only include reviews with actual written text (> 20 chars)
        if (review.text && review.text.length > 20) {
            reviews.push(review);
        }
    });

    return reviews;
}"""


def _parse_hours_from_aria_label(hours_raw: str) -> dict[str, str]:
    """Parse an hours aria-label string like 'Hours: Monday, 9 AM to 5 PM; Tuesday, ...'
    into a day->hours dict."""
    hours: dict[str, str] = {}
    if not hours_raw:
        return hours

    # Remove the "Hours: " or "Hours " prefix
    text = hours_raw.replace("Hours:", "").replace("Hours", "").strip()

    # Split by semicolons or periods to get individual day entries
    import re
    entries = re.split(r'[;.]', text)
    for entry in entries:
        entry = entry.strip()
        if not entry:
            continue
        # Try to split on first comma: "Monday, 9 AM to 5 PM"
        parts = entry.split(',', 1)
        if len(parts) == 2:
            day = parts[0].strip()
            time_str = parts[1].strip()
            if day and time_str:
                hours[day] = time_str
        elif entry:
            # Might be "Open 24 hours" or similar
            hours["Note"] = entry
    return hours


async def _notify(callback: ProgressCallback, step: str, message: str) -> None:
    """Send a progress notification via the callback if provided."""
    if callback is not None:
        try:
            await callback({"step": step, "message": message})
        except Exception as exc:
            logger.debug("Progress callback error (non-fatal): %s", exc)


def _clean_photo_url(src: str) -> str | None:
    """Normalise a Google photo URL to a high-res version.

    Returns None for non-photo URLs (data URIs, avatars, tiny icons).
    """
    if not src or src.startswith("data:"):
        return None
    if "googleusercontent" not in src:
        return None
    # Skip reviewer avatars / profile pics (small, marked with -rp-mo)
    if "-rp-mo" in src or "s40-k" in src or "s36-" in src or "w36-" in src:
        return None
    # Must be a business photo (contains /p/ or /gps-cs or /gps-proxy)
    if not any(seg in src for seg in ["/p/", "/gps-cs", "/gps-proxy"]):
        return None
    # Get the base URL without size params and set high-res
    base = src.split("=")[0]
    return base + "=w800-h600-k-no"


async def extract_photos(page: Page, max_photos: int = 8) -> list[str]:
    """
    Extract business photo URLs from a Google Maps page.

    Strategy:
      1. First grab any photos already visible on the overview page (hero + thumbnails).
      2. Then click the Photos tab and collect from the photo grid.
      3. Deduplicate by base URL (before the =wNNN params).

    Args:
        page: The Playwright page already on the business listing.
        max_photos: Maximum number of photo URLs to collect.

    Returns:
        List of unique photo URL strings. May be empty if extraction fails.
    """
    seen_bases: set[str] = set()
    photos: list[str] = []

    def _add(url: str) -> None:
        clean = _clean_photo_url(url)
        if clean and clean.split("=")[0] not in seen_bases and len(photos) < max_photos:
            seen_bases.add(clean.split("=")[0])
            photos.append(clean)

    try:
        # ── Phase 1: Grab photos already on the overview page ──
        overview_urls = await page.evaluate("""() => {
            const urls = [];
            // Hero image and thumbnail grid on the overview page
            // Google uses both /p/ and /gps-cs-s/ paths for business photos
            const imgs = document.querySelectorAll(
                'img[src*="googleusercontent.com/p/"],' +
                'img[src*="googleusercontent.com/gps-cs"],' +
                'img[src*="googleusercontent.com/gps-proxy"],' +
                '[data-photo-index] img[src*="googleusercontent"],' +
                'button[aria-label*="Photo"] img[src*="googleusercontent"]'
            );
            for (const img of imgs) {
                const src = img.src || img.getAttribute('data-src') || '';
                if (src && !src.startsWith('data:') && src.includes('googleusercontent')) {
                    urls.push(src);
                }
            }
            return urls;
        }""")

        for u in (overview_urls or []):
            _add(u)

        # ── Phase 2: Click Photos tab for more images ──
        if len(photos) < max_photos:
            photos_tab = await page.query_selector(
                'button[aria-label*="Photo"], '
                'button[data-tab-id="photos"], '
                'a[aria-label*="Photos"], '
                'button[jsaction*="photos"], '
                'button:has-text("Photos")'
            )
            if photos_tab:
                await photos_tab.click()
                await asyncio.sleep(2)

                # Wait for photo grid to load
                try:
                    await page.wait_for_selector(
                        '[data-photo-index] img, '
                        'img[decoding="async"][src*="googleusercontent"]',
                        timeout=5000,
                    )
                    await asyncio.sleep(1)
                except Exception:
                    pass

                # Scroll once to load more thumbnails
                scrollable = await page.query_selector(
                    'div.m6QErb, div[role="main"]'
                )
                if scrollable:
                    try:
                        await scrollable.evaluate('(el) => el.scrollBy(0, 600)')
                        await asyncio.sleep(1)
                    except Exception:
                        pass

                grid_urls = await page.evaluate("""() => {
                    const urls = [];
                    const selectors = [
                        '[data-photo-index] img',
                        'a[data-photo-index] img',
                        'button[data-photo-index] img',
                        'div.U39Pmb img',
                        'img[decoding="async"][src*="googleusercontent"]',
                        'img[src*="lh3.googleusercontent"]',
                        'img[src*="lh5.googleusercontent"]',
                        'img[src*="googleusercontent.com/gps-cs"]',
                        'img[src*="googleusercontent.com/gps-proxy"]',
                    ];
                    for (const sel of selectors) {
                        const imgs = document.querySelectorAll(sel);
                        for (const img of imgs) {
                            const src = img.src || img.getAttribute('data-src') || '';
                            if (src && !src.startsWith('data:') && src.includes('googleusercontent')) {
                                urls.push(src);
                            }
                        }
                    }
                    return urls;
                }""")

                for u in (grid_urls or []):
                    _add(u)

    except Exception as exc:
        logger.warning("Photo extraction failed (non-fatal): %s", exc)

    return photos


async def extract_reviews(page: Page, max_reviews: int = 10) -> list[dict[str, Any]]:
    """
    Click the Reviews tab, scroll to load content, and extract review data.
    Uses the proven getrankedlocal production selectors.
    Entire operation is capped at 20 seconds to avoid blocking the pipeline.

    Args:
        page: The Playwright page already on the business listing.
        max_reviews: Maximum number of reviews to collect.

    Returns:
        List of review dicts with keys: author, rating, text, time, helpful.
    """
    reviews: list[dict[str, Any]] = []

    async def _do_extract() -> list[dict[str, Any]]:
        # Click the Reviews tab - production selectors
        # Only proceed if a Reviews tab actually exists
        reviews_tab = await page.query_selector(
            'button[aria-label*="Reviews"], '
            'button[role="tab"]:has-text("Reviews")'
        )
        if not reviews_tab:
            reviews_tab = await page.query_selector('button:has-text("Reviews")')

        if not reviews_tab:
            logger.info("No Reviews tab found - business may have too few reviews")
            return []

        await reviews_tab.click()
        await asyncio.sleep(1.5)

        # Scroll the review feed to load more reviews — 3 quick scrolls
        review_feed = await page.query_selector(
            '[role="feed"], .m6QErb[aria-label*="Reviews"], .m6QErb.DxyBCb'
        )
        if review_feed:
            for _ in range(3):
                await review_feed.evaluate('(element) => element.scrollTop = element.scrollHeight')
                await asyncio.sleep(0.8)

        # Expand truncated review text by clicking "More" buttons
        more_buttons = await page.query_selector_all(
            'button.w8nwRe, button[aria-label="See more"], '
            'button.M77dve, a.review-more-link'
        )
        for btn in more_buttons[:max_reviews]:
            try:
                await btn.click()
                await asyncio.sleep(0.1)
            except Exception:
                pass

        # Extract review data — uses .MyEned / .wiI7pd for actual review text
        return await page.evaluate(EXTRACT_REVIEWS_JS, max_reviews)

    try:
        reviews = await asyncio.wait_for(_do_extract(), timeout=20)
    except asyncio.TimeoutError:
        logger.warning("Review extraction timed out after 20s (non-fatal)")
    except Exception as exc:
        logger.warning("Review extraction failed (non-fatal): %s", exc)

    return reviews


async def scrape_business_from_maps(
    place_id: Optional[str] = None,
    cid: Optional[str] = None,
    business_name: Optional[str] = None,
    raw_url: Optional[str] = None,
    callback: ProgressCallback = None,
) -> BusinessData:
    """
    Scrape a single business from Google Maps and return comprehensive data
    suitable for generating a website.

    The preferred approach is to pass the original Google Maps URL (raw_url)
    since it contains the data segments that uniquely identify the business
    and loads the business panel reliably. CID/place_id/name are used as
    fallbacks for URL construction.

    Args:
        place_id: Google Maps place ID (e.g. "ChIJ...")
        cid: Google Maps CID numeric identifier
        business_name: Business name to search for (fallback)
        raw_url: The original Google Maps URL pasted by the user (preferred)
        callback: Optional async callable for progress updates.

    Returns:
        BusinessData pydantic model with all extracted fields.

    Raises:
        ValueError: If no identifiers are provided.
    """
    if not any([place_id, cid, business_name, raw_url]):
        raise ValueError("At least one of raw_url, place_id, cid, or business_name must be provided")

    context = None

    async with async_playwright() as pw:
        try:
            await _notify(callback, "launching_browser", "Starting browser...")

            import os
            has_display = bool(os.environ.get("DISPLAY"))
            use_headless = not has_display

            # ── Use persistent context with per-job copy ──
            # launch_persistent_context saves cookies/profile across runs.
            # This is CRITICAL: Google Maps shows the full experience (Reviews,
            # Photos, Menu tabs) only when the browser has an established Google
            # session. Without it, Maps serves a "limited view" with only
            # Overview + About tabs. The persistent profile stores the consent
            # cookies from visiting google.com first.
            #
            # To support concurrent scrapes, we copy the base profile to a
            # unique temp directory per job so multiple Chromium instances
            # don't fight over the SingletonLock.
            import shutil
            import tempfile

            base_profile_dir = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                ".chrome-profile",
            )
            # Create base profile dir if it doesn't exist yet
            os.makedirs(base_profile_dir, exist_ok=True)

            # Copy base profile to a temp dir for this scrape job
            # Skip stale Chrome lock/socket files (Singleton*) that can't be copied
            job_profile_dir = tempfile.mkdtemp(prefix="chrome_profile_")
            if os.listdir(base_profile_dir):
                def _ignore_locks(d: str, files: list[str]) -> list[str]:
                    return [f for f in files if f.startswith("Singleton")]
                shutil.copytree(base_profile_dir, job_profile_dir, dirs_exist_ok=True, ignore=_ignore_locks)

            context = await pw.chromium.launch_persistent_context(
                job_profile_dir,
                headless=use_headless,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-blink-features=AutomationControlled",
                    "--window-size=1920,1080",
                ],
                viewport={"width": 1920, "height": 1080},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/131.0.0.0 Safari/537.36"
                ),
                locale="en-US",
                timezone_id="America/New_York",
                permissions=["geolocation"],
            )

            page = context.pages[0] if context.pages else await context.new_page()

            # ── Establish Google session ──
            # Visit google.com first to accept cookies and get a session.
            # This makes Google Maps show the FULL view with all tabs.
            await page.goto("https://www.google.com/?hl=en", wait_until="load", timeout=15000)
            await asyncio.sleep(2)

            # Accept cookie consent if prompted
            try:
                consent_btn = await page.query_selector(
                    'button:has-text("Accept all"), '
                    'button:has-text("I agree"), '
                    'button[aria-label="Accept all"]'
                )
                if consent_btn:
                    await consent_btn.click()
                    await asyncio.sleep(1)
            except Exception:
                pass

            # ── Build a SEARCH URL ──
            # Google Maps resolves search URLs to full place pages with all
            # tabs (Overview, Menu, Reviews, About). Direct place URLs with
            # stale data segments often fail or show the limited view.
            from urllib.parse import quote_plus, unquote
            import re

            search_query = ""
            if raw_url and "google.com/maps" in raw_url:
                # Extract business name from the URL path segment
                place_match = re.search(r"/place/([^/@]+)", raw_url)
                if place_match:
                    search_query = unquote(place_match.group(1)).replace("+", " ")
                if not search_query and business_name:
                    search_query = business_name

            if not search_query and business_name:
                search_query = business_name

            if search_query:
                url = f"https://www.google.com/maps/search/{quote_plus(search_query)}?hl=en"
                await _notify(callback, "navigating", f"Searching Google Maps for: {search_query}")
            elif cid:
                url = f"https://www.google.com/maps?cid={cid}&hl=en"
                await _notify(callback, "navigating", f"Navigating via CID: {cid}")
            elif place_id:
                url = f"https://www.google.com/maps/place/?q=place_id:{place_id}&hl=en"
                await _notify(callback, "navigating", f"Navigating via place_id: {place_id}")
            else:
                raise ValueError("Could not build a navigation URL")

            # Navigate to Maps — full JS load needed for SPA
            await page.goto(url, wait_until="load", timeout=45000)
            await asyncio.sleep(5)

            # Handle cookie consent dialog on Maps if it appears
            try:
                consent_btn = await page.query_selector(
                    'button[aria-label="Accept all"], '
                    'form[action*="consent"] button, '
                    'button:has-text("Accept all")'
                )
                if consent_btn:
                    await consent_btn.click()
                    await asyncio.sleep(2)
            except Exception:
                pass

            # If search returned a list instead of auto-resolving, click first
            # NON-SPONSORED result. Sponsored listings appear at the top with
            # a "Sponsored" label and should be skipped.
            try:
                results = await page.query_selector_all(
                    '[role="article"], a.hfpxzc, div.Nv2PK'
                )
                clicked = False
                for result in results:
                    # Check if this result or its parent contains "Sponsored" text
                    is_sponsored = await result.evaluate("""(el) => {
                        const text = el.innerText || '';
                        const parent = el.closest('[role="article"]') || el.parentElement;
                        const parentText = parent ? (parent.innerText || '') : '';
                        const combined = text + ' ' + parentText;
                        return combined.includes('Sponsored') ||
                               combined.includes('sponsored') ||
                               combined.includes('Ad ·') ||
                               combined.includes('Реклама');
                    }""")
                    if not is_sponsored:
                        link = await result.query_selector('a') if await result.get_attribute('href') is None else result
                        await (link or result).click()
                        clicked = True
                        await asyncio.sleep(4)
                        break
                # Fallback: if all results look sponsored, click the first one anyway
                if not clicked and results:
                    first_link = await results[0].query_selector('a') or results[0]
                    await first_link.click()
                    await asyncio.sleep(4)
            except Exception:
                pass

            logger.info("Resolved URL: %s", page.url)

            # Wait for the business profile panel to load
            try:
                await page.wait_for_selector(
                    'h1[aria-label], h1.DUwDvf, [data-item-id="address"], h1',
                    timeout=10000,
                )
            except Exception:
                logger.warning("Business heading not found - page may not have loaded fully")

            await asyncio.sleep(2)

            # ── Log which tabs are visible (diagnostic) ──
            tabs_info = await page.evaluate("""() => {
                const tabs = [];
                const tabButtons = document.querySelectorAll(
                    'button[role="tab"], button[aria-label*="Overview"], ' +
                    'button[aria-label*="Reviews"], button[aria-label*="About"], ' +
                    'button[aria-label*="Photos"], button[aria-label*="Menu"]'
                );
                tabButtons.forEach(btn => {
                    tabs.push(btn.innerText || btn.getAttribute('aria-label') || 'unknown');
                });
                return tabs;
            }""")
            logger.info("Available tabs on page: %s", tabs_info)

            # Scroll the side panel down to load services, reviews button, etc.
            side_panel = await page.query_selector(
                'div.m6QErb.DxyBCb, div[role="main"] div.m6QErb, div.bJzME'
            )
            if side_panel:
                for _ in range(3):
                    try:
                        await side_panel.evaluate('(el) => el.scrollBy(0, 300)')
                        await asyncio.sleep(0.5)
                    except Exception:
                        break
                # Scroll back to top for consistent extraction
                try:
                    await side_panel.evaluate('(el) => el.scrollTop = 0')
                    await asyncio.sleep(0.5)
                except Exception:
                    pass

            # ---- Extract main profile data ----
            await _notify(callback, "extracting_profile", "Extracting business profile data...")
            profile_data = await page.evaluate(EXTRACT_PROFILE_JS)

            if not profile_data.get("name"):
                if business_name:
                    profile_data["name"] = business_name
                else:
                    raise ValueError(
                        "Could not extract business name from the page. "
                        "The business may not exist or the page failed to load."
                    )

            await _notify(
                callback,
                "extracting_profile",
                f"Got business name: {profile_data.get('name', 'unknown')}",
            )

            # Parse hours from aria-label if table hours weren't found
            hours_dict = profile_data.get("hours")
            if not hours_dict and profile_data.get("hours_raw"):
                hours_dict = _parse_hours_from_aria_label(profile_data["hours_raw"])

            # Try expanding hours if still not found
            if not hours_dict:
                try:
                    hours_btn = await page.query_selector(
                        '[data-item-id="oh"], '
                        'button[aria-label*="hour"], '
                        'div[aria-label*="hour"] button'
                    )
                    if hours_btn:
                        await hours_btn.click()
                        await asyncio.sleep(1.5)
                        hours_data = await page.evaluate("""() => {
                            const hours = {};
                            const rows = document.querySelectorAll(
                                'table.eK4R0e tr, table.WgFkxc tr, ' +
                                'table.y0skZc tr, div[aria-label*="hour"] table tr'
                            );
                            for (const row of rows) {
                                const cells = row.querySelectorAll('td');
                                if (cells.length >= 2) {
                                    const day = cells[0].innerText.trim();
                                    const time = cells[1].innerText.trim();
                                    if (day && time) hours[day] = time;
                                }
                            }
                            return Object.keys(hours).length > 0 ? hours : null;
                        }""")
                        if hours_data:
                            hours_dict = hours_data
                except Exception:
                    pass

            # ---- Extract photos ----
            await _notify(callback, "extracting_photos", "Extracting business photos...")
            photo_urls = await extract_photos(page, max_photos=6)
            if photo_urls:
                await _notify(
                    callback,
                    "extracting_photos",
                    f"Found {len(photo_urls)} photos",
                )

            # Navigate back to main business page before extracting reviews
            if photo_urls:
                overview_tab = await page.query_selector(
                    'button[aria-label*="Overview"], '
                    'button[data-tab-id="overview"], '
                    'button:has-text("Overview")'
                )
                if overview_tab:
                    await overview_tab.click()
                    await asyncio.sleep(1.5)
                else:
                    await page.goto(url, wait_until="domcontentloaded", timeout=15000)
                    await asyncio.sleep(2)

            # ---- Extract reviews ----
            await _notify(callback, "extracting_reviews", "Extracting business reviews...")
            review_data = await extract_reviews(page, max_reviews=15)
            if review_data:
                await _notify(
                    callback,
                    "extracting_reviews",
                    f"Found {len(review_data)} reviews",
                )

            # ---- Build the final BusinessData model ----
            await _notify(callback, "building_result", "Assembling business data...")

            business = BusinessData(
                name=profile_data["name"],
                address=profile_data.get("address"),
                phone=profile_data.get("phone"),
                website=profile_data.get("website"),
                rating=profile_data.get("rating"),
                review_count=profile_data.get("review_count"),
                category=profile_data.get("category"),
                description=profile_data.get("description"),
                hours=hours_dict if hours_dict else None,
                hours_raw=profile_data.get("hours_raw"),
                services=profile_data.get("services"),
                photos=photo_urls if photo_urls else None,
                reviews=review_data if review_data else None,
                latitude=profile_data.get("latitude"),
                longitude=profile_data.get("longitude"),
                place_id=place_id,
                cid=cid or profile_data.get("cid"),
                open_now=profile_data.get("open_now"),
                status_text=profile_data.get("status_text"),
                photo_count=profile_data.get("photo_count"),
                review_topics=profile_data.get("review_topics"),
                price_info=profile_data.get("price_info"),
                has_menu=profile_data.get("has_menu"),
                links=profile_data.get("links"),
            )

            await _notify(callback, "complete", f"Successfully scraped: {business.name}")
            return business

        except Exception as exc:
            logger.error("Maps scraping failed: %s", exc)
            await _notify(callback, "error", f"Scraping failed: {exc}")
            raise

        finally:
            if context:
                await context.close()
            # Clean up temp profile directory
            if job_profile_dir and os.path.exists(job_profile_dir):
                shutil.rmtree(job_profile_dir, ignore_errors=True)


if __name__ == "__main__":
    import json
    import sys

    async def _main() -> None:
        cid_val: Optional[str] = None
        place_id_val: Optional[str] = None
        name_val: Optional[str] = None

        args = sys.argv[1:]
        positional: list[str] = []

        for arg in args:
            if arg.startswith("--cid="):
                cid_val = arg.split("=", 1)[1]
            elif arg.startswith("--place-id="):
                place_id_val = arg.split("=", 1)[1]
            else:
                positional.append(arg)

        if positional:
            name_val = " ".join(positional)

        if not any([cid_val, place_id_val, name_val]):
            print("Usage: python maps_scraper.py [--cid=<cid>] [--place-id=<id>] [business name]")
            sys.exit(1)

        async def progress_printer(data: dict[str, str]) -> None:
            print(f"  [{data['step']}] {data['message']}")

        print("Scraping Google Maps business...")
        result = await scrape_business_from_maps(
            place_id=place_id_val,
            cid=cid_val,
            business_name=name_val,
            callback=progress_printer,
        )

        print(f"\n{'=' * 60}")
        print(f"Business: {result.name}")
        print(f"Address:  {result.address or 'N/A'}")
        print(f"Phone:    {result.phone or 'N/A'}")
        print(f"Website:  {result.website or 'N/A'}")
        print(f"Rating:   {result.rating or 'N/A'} ({result.review_count or 0} reviews)")
        print(f"Category: {result.category or 'N/A'}")
        print(f"Coords:   {result.latitude}, {result.longitude}")

        if result.hours:
            print("\nHours:")
            for day, hrs in result.hours.items():
                print(f"  {day}: {hrs}")

        if result.services:
            print(f"\nServices: {', '.join(result.services)}")

        if result.photos:
            print(f"\nPhotos ({len(result.photos)}):")
            for u in result.photos:
                print(f"  {u[:100]}...")

        if result.reviews:
            print(f"\nReviews ({len(result.reviews)}):")
            for rev in result.reviews:
                stars = f"{'*' * rev.get('rating', 0)}" if rev.get("rating") else ""
                print(f"  {rev.get('author', 'Anonymous')} {stars} ({rev.get('time', '')})")
                text = rev.get("text", "")
                if text:
                    print(f"    {text[:120]}{'...' if len(text) > 120 else ''}")

        import os
        os.makedirs("tmp_scripts", exist_ok=True)
        output_path = "tmp_scripts/maps_business.json"
        with open(output_path, "w") as f:
            json.dump(result.model_dump(), f, indent=2, default=str)
        print(f"\nFull data saved to {output_path}")

    asyncio.run(_main())
