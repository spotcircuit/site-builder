"""
Google Maps Business Scraper

Scrapes a single business from Google Maps using Playwright.
Extracts all data needed to generate a website: profile info, photos, reviews,
hours, services, and location coordinates.

Adapted from the lead_finder project's scraper pattern but focused on
comprehensive single-business data extraction.
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
    website: Optional[str] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    category: Optional[str] = None
    hours: Optional[dict[str, str]] = Field(default=None, description="Day -> hours string mapping")
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


# JavaScript to extract the main business profile data from the Google Maps DOM.
# Runs in-page to avoid multiple round trips. Returns a flat dict of extracted fields.
EXTRACT_PROFILE_JS = """() => {
    const data = {};

    // Business name - the main heading
    const nameEl = document.querySelector('h1.DUwDvf, h1[data-attrid="title"], h1');
    if (nameEl) data.name = nameEl.innerText.trim();

    // Address - look for the address button/div
    const addrEl = document.querySelector(
        'button[data-item-id="address"] .Io6YTe, ' +
        'button[data-item-id="address"] .rogA2c, ' +
        '[data-item-id="address"]'
    );
    if (addrEl) data.address = addrEl.innerText.trim();

    // Phone
    const phoneEl = document.querySelector(
        'button[data-item-id^="phone:"] .Io6YTe, ' +
        'button[data-item-id^="phone:"] .rogA2c, ' +
        '[data-item-id^="phone:"]'
    );
    if (phoneEl) {
        let phoneText = phoneEl.innerText.trim();
        // Extract just the phone number if there's extra text
        const phoneMatch = phoneText.match(/[\\d()\\s.+-]{7,}/);
        if (phoneMatch) data.phone = phoneMatch[0].trim();
        else data.phone = phoneText;
    }

    // Website
    const webEl = document.querySelector(
        'a[data-item-id="authority"], ' +
        'button[data-item-id="authority"] .Io6YTe, ' +
        '[data-item-id="authority"]'
    );
    if (webEl) {
        data.website = webEl.getAttribute('href') || webEl.innerText.trim();
    }

    // Rating
    const ratingEl = document.querySelector(
        'div.F7nice span[aria-hidden="true"], ' +
        'span.ceNzKf, ' +
        'div.fontDisplayLarge'
    );
    if (ratingEl) {
        const val = parseFloat(ratingEl.innerText.trim().replace(',', '.'));
        if (!isNaN(val) && val > 0 && val <= 5) data.rating = val;
    }

    // Review count
    const reviewCountEl = document.querySelector(
        'div.F7nice span[aria-label*="review"], ' +
        'span.RDApEe, ' +
        'button[jsaction*="review"] span'
    );
    if (reviewCountEl) {
        const text = reviewCountEl.innerText || reviewCountEl.getAttribute('aria-label') || '';
        const countMatch = text.replace(/,/g, '').match(/(\\d+)/);
        if (countMatch) data.review_count = parseInt(countMatch[1]);
    }

    // Category
    const catEl = document.querySelector(
        'button[jsaction*="category"] .DkEaL, ' +
        'button.DkEaL, ' +
        'span.DkEaL'
    );
    if (catEl) data.category = catEl.innerText.trim();

    // Hours - from the hours table/section
    const hours = {};
    const hourRows = document.querySelectorAll(
        'table.eK4R0e tr, ' +
        'table.WgFkxc tr, ' +
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
    if (Object.keys(hours).length > 0) data.hours = hours;

    // If no hours table found, try the collapsed hours display
    if (!data.hours) {
        const hoursBtn = document.querySelector(
            '[data-item-id="oh"] .Io6YTe, ' +
            'div[aria-label*="hours"] .Io6YTe'
        );
        if (hoursBtn) {
            data.hours_summary = hoursBtn.innerText.trim();
        }
    }

    // Services - from the services/amenities sections
    const serviceEls = document.querySelectorAll(
        'div[data-attrid*="service"] li, ' +
        'div.LQjNnc span, ' +
        'div[aria-label*="Service"] span.hYBQ4b'
    );
    const services = [];
    for (const el of serviceEls) {
        const txt = el.innerText.trim();
        if (txt && txt.length < 100 && !services.includes(txt)) {
            services.push(txt);
        }
    }
    if (services.length > 0) data.services = services;

    // Coordinates from the page URL
    const url = window.location.href;
    const coordMatch = url.match(/@(-?\\d+\\.\\d+),(-?\\d+\\.\\d+)/);
    if (coordMatch) {
        data.latitude = parseFloat(coordMatch[1]);
        data.longitude = parseFloat(coordMatch[2]);
    }

    // Place ID from URL
    const placeMatch = url.match(/place\\/[^/]+\\/([^/]+)/);
    if (placeMatch) data.url_place_segment = placeMatch[1];

    // CID from URL params or data attributes
    const cidMatch = url.match(/[?&]cid=(\\d+)/);
    if (cidMatch) data.cid = cidMatch[1];

    return data;
}"""


async def _notify(callback: ProgressCallback, step: str, message: str) -> None:
    """Send a progress notification via the callback if provided."""
    if callback is not None:
        try:
            await callback({"step": step, "message": message})
        except Exception as exc:
            logger.debug("Progress callback error (non-fatal): %s", exc)


async def extract_photos(page: Page, max_photos: int = 6) -> list[str]:
    """
    Click the Photos tab on a Google Maps business page and extract image URLs.

    Args:
        page: The Playwright page already on the business listing.
        max_photos: Maximum number of photo URLs to collect.

    Returns:
        List of photo URL strings. May be empty if extraction fails.
    """
    photos: list[str] = []

    try:
        # Click the Photos tab - try multiple selectors
        photos_tab = await page.query_selector(
            'button[aria-label*="Photo"], '
            'button[data-tab-id="photos"], '
            'a[href*="tab=photos"], '
            'button[jsaction*="photos"]'
        )
        if not photos_tab:
            # Try clicking by text content
            photos_tab = await page.query_selector('button:has-text("Photos")')

        if photos_tab:
            await photos_tab.click()
            await asyncio.sleep(2)

            # Wait for photo grid to load
            await page.wait_for_selector(
                'div[data-photo-index] img, '
                'div.U39Pmb img, '
                'div[role="img"], '
                'a[data-photo-index] img, '
                'button[data-photo-index] img',
                timeout=5000,
            )
            await asyncio.sleep(1)

        # Extract image URLs from the page - photos can appear in grid or carousel
        photo_urls = await page.evaluate(f"""() => {{
            const urls = new Set();
            const maxCount = {max_photos};

            // Try multiple selectors for photo elements
            const selectors = [
                'div[data-photo-index] img',
                'a[data-photo-index] img',
                'button[data-photo-index] img',
                'div.U39Pmb img',
                'img.Uf0tqf',
                'img[decoding="async"][src*="googleusercontent"]',
                'img[src*="lh5.googleusercontent"]',
                'img[src*="lh3.googleusercontent"]',
            ];

            for (const selector of selectors) {{
                if (urls.size >= maxCount) break;
                const imgs = document.querySelectorAll(selector);
                for (const img of imgs) {{
                    if (urls.size >= maxCount) break;
                    const src = img.src || img.getAttribute('data-src') || '';
                    // Only include real Google photo URLs, skip data: URIs and icons
                    if (src && !src.startsWith('data:') && src.includes('google')) {{
                        // Attempt to get a higher-resolution version by modifying the URL params
                        let cleanUrl = src.split('=')[0];
                        if (cleanUrl.includes('googleusercontent')) {{
                            cleanUrl += '=w800-h600-no';
                        }} else {{
                            cleanUrl = src;
                        }}
                        urls.add(cleanUrl);
                    }}
                }}
            }}

            return Array.from(urls);
        }}""")

        if photo_urls:
            photos = photo_urls[:max_photos]

    except Exception as exc:
        logger.warning("Photo extraction failed (non-fatal): %s", exc)

    return photos


async def extract_reviews(page: Page, max_reviews: int = 5) -> list[dict[str, Any]]:
    """
    Click the Reviews tab on a Google Maps business page, scroll once to load
    content, and extract review data.

    Args:
        page: The Playwright page already on the business listing.
        max_reviews: Maximum number of reviews to collect.

    Returns:
        List of review dicts with keys: author, rating, text, time.
        May be empty if extraction fails.
    """
    reviews: list[dict[str, Any]] = []

    try:
        # Click the Reviews tab
        reviews_tab = await page.query_selector(
            'button[aria-label*="Review"], '
            'button[data-tab-id="reviews"], '
            'a[href*="tab=reviews"], '
            'button[jsaction*="review"]'
        )
        if not reviews_tab:
            reviews_tab = await page.query_selector('button:has-text("Reviews")')

        if reviews_tab:
            await reviews_tab.click()
            await asyncio.sleep(2)

        # Wait for reviews to load
        await page.wait_for_selector(
            'div.jftiEf, div[data-review-id], div.WMbnJf',
            timeout=5000,
        )

        # Scroll once within the reviews pane to load more
        scrollable = await page.query_selector(
            'div.m6QErb.DxyBCb, div.m6QErb[role="feed"], div.section-scrollbox'
        )
        if scrollable:
            await scrollable.evaluate('el => el.scrollBy(0, 800)')
            await asyncio.sleep(1.5)

        # Expand truncated review text by clicking "More" buttons
        more_buttons = await page.query_selector_all(
            'button.w8nwRe, button[aria-label="See more"], '
            'button.M77dve, a.review-more-link'
        )
        for btn in more_buttons[:max_reviews]:
            try:
                await btn.click()
                await asyncio.sleep(0.3)
            except Exception:
                pass

        # Extract review data
        reviews = await page.evaluate(f"""() => {{
            const results = [];
            const maxCount = {max_reviews};

            const reviewEls = document.querySelectorAll(
                'div.jftiEf, div[data-review-id], div.WMbnJf'
            );

            for (const el of reviewEls) {{
                if (results.length >= maxCount) break;
                const review = {{}};

                // Author name
                const authorEl = el.querySelector(
                    'div.d4r55, span.d4r55, a.WNxzHc, div.TSUbDb a'
                );
                if (authorEl) review.author = authorEl.innerText.trim();

                // Star rating
                const starsEl = el.querySelector(
                    'span.kvMYJc, span[role="img"][aria-label*="star"]'
                );
                if (starsEl) {{
                    const label = starsEl.getAttribute('aria-label') || '';
                    const starMatch = label.match(/(\\d+)/);
                    if (starMatch) review.rating = parseInt(starMatch[1]);
                }}

                // Review text
                const textEl = el.querySelector(
                    'span.wiI7pd, div.MyEned span, div.review-full-text'
                );
                if (textEl) review.text = textEl.innerText.trim();

                // Time / relative date
                const timeEl = el.querySelector(
                    'span.rsqaWe, span.dehysf, span.review-date'
                );
                if (timeEl) review.time = timeEl.innerText.trim();

                // Only include reviews that have at least some content
                if (review.author || review.text) {{
                    results.push(review);
                }}
            }}

            return results;
        }}""")

    except Exception as exc:
        logger.warning("Review extraction failed (non-fatal): %s", exc)

    return reviews


async def scrape_business_from_maps(
    place_id: Optional[str] = None,
    cid: Optional[str] = None,
    business_name: Optional[str] = None,
    callback: ProgressCallback = None,
) -> BusinessData:
    """
    Scrape a single business from Google Maps and return comprehensive data
    suitable for generating a website.

    The function navigates to the business page using one of:
    - CID (preferred, most stable identifier)
    - place_id
    - business_name (search fallback)

    Args:
        place_id: Google Maps place ID (e.g. "ChIJ...")
        cid: Google Maps CID numeric identifier
        business_name: Business name to search for (fallback)
        callback: Optional async callable for progress updates. Receives dicts
                  like {"step": "extracting_profile", "message": "Got business name..."}

    Returns:
        BusinessData pydantic model with all extracted fields.

    Raises:
        ValueError: If none of place_id, cid, or business_name are provided.
    """
    if not any([place_id, cid, business_name]):
        raise ValueError("At least one of place_id, cid, or business_name must be provided")

    browser: Optional[Browser] = None

    async with async_playwright() as pw:
        try:
            await _notify(callback, "launching_browser", "Starting headless browser...")

            browser = await pw.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-blink-features=AutomationControlled",
                    "--window-size=1280,720",
                ],
            )

            context = await browser.new_context(
                viewport={"width": 1280, "height": 720},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                locale="en-US",
            )
            page = await context.new_page()

            # Build the navigation URL based on available identifiers
            if cid:
                url = f"https://www.google.com/maps?cid={cid}"
                await _notify(callback, "navigating", f"Navigating to business via CID: {cid}")
            elif place_id:
                url = f"https://www.google.com/maps/place/?q=place_id:{place_id}"
                await _notify(callback, "navigating", f"Navigating to business via place_id: {place_id}")
            else:
                # Search by name as a fallback
                from urllib.parse import quote_plus
                query = quote_plus(business_name)  # type: ignore[arg-type]
                url = f"https://www.google.com/maps/search/{query}"
                await _notify(callback, "navigating", f"Searching Google Maps for: {business_name}")

            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(3)

            # Handle cookie consent dialog if it appears (common in EU regions)
            try:
                consent_btn = await page.query_selector(
                    'button[aria-label="Accept all"], '
                    'form[action*="consent"] button, '
                    'button:has-text("Accept all")'
                )
                if consent_btn:
                    await consent_btn.click()
                    await asyncio.sleep(1)
            except Exception:
                pass

            # If we searched by name, we may land on search results rather than
            # a single business page. Click the first result if so.
            if business_name and not cid and not place_id:
                try:
                    first_result = await page.query_selector(
                        'a.hfpxzc, div.Nv2PK a, a[href*="/maps/place/"]'
                    )
                    if first_result:
                        await first_result.click()
                        await asyncio.sleep(3)
                except Exception:
                    pass

            # Wait for the business profile to load
            try:
                await page.wait_for_selector(
                    "h1.DUwDvf, h1[data-attrid='title'], h1",
                    timeout=10000,
                )
            except Exception:
                logger.warning("Business heading not found - page may not have loaded fully")

            await asyncio.sleep(1)

            # ---- Extract main profile data ----
            await _notify(callback, "extracting_profile", "Extracting business profile data...")
            profile_data = await page.evaluate(EXTRACT_PROFILE_JS)

            if not profile_data.get("name"):
                # Fallback: use the provided business_name or raise
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

            # Try to expand hours if they are collapsed
            if not profile_data.get("hours"):
                try:
                    hours_btn = await page.query_selector(
                        '[data-item-id="oh"], '
                        'button[aria-label*="hour"], '
                        'div[aria-label*="hour"] button'
                    )
                    if hours_btn:
                        await hours_btn.click()
                        await asyncio.sleep(1.5)
                        # Re-extract hours after expanding
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
                            profile_data["hours"] = hours_data
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

            # Navigate back to the main business page before extracting reviews
            # (the Photos tab may have changed the view)
            if photo_urls:
                # Click the Overview tab to get back
                overview_tab = await page.query_selector(
                    'button[aria-label*="Overview"], '
                    'button[data-tab-id="overview"], '
                    'button:has-text("Overview")'
                )
                if overview_tab:
                    await overview_tab.click()
                    await asyncio.sleep(1.5)
                else:
                    # Fallback: navigate back to the original URL
                    await page.goto(url, wait_until="domcontentloaded", timeout=15000)
                    await asyncio.sleep(2)

            # ---- Extract reviews ----
            await _notify(callback, "extracting_reviews", "Extracting business reviews...")
            review_data = await extract_reviews(page, max_reviews=5)
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
                hours=profile_data.get("hours"),
                services=profile_data.get("services"),
                photos=photo_urls if photo_urls else None,
                reviews=review_data if review_data else None,
                latitude=profile_data.get("latitude"),
                longitude=profile_data.get("longitude"),
                place_id=place_id,
                cid=cid or profile_data.get("cid"),
            )

            await _notify(callback, "complete", f"Successfully scraped: {business.name}")
            return business

        except Exception as exc:
            logger.error("Maps scraping failed: %s", exc)
            await _notify(callback, "error", f"Scraping failed: {exc}")
            raise

        finally:
            if browser:
                await browser.close()


if __name__ == "__main__":
    import json
    import sys

    async def _main() -> None:
        # Accept either --cid=<value>, --place-id=<value>, or a business name as args
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
            for url in result.photos:
                print(f"  {url[:100]}...")

        if result.reviews:
            print(f"\nReviews ({len(result.reviews)}):")
            for rev in result.reviews:
                stars = f"{'*' * rev.get('rating', 0)}" if rev.get("rating") else ""
                print(f"  {rev.get('author', 'Anonymous')} {stars} ({rev.get('time', '')})")
                text = rev.get("text", "")
                if text:
                    print(f"    {text[:120]}{'...' if len(text) > 120 else ''}")

        # Save full JSON output
        import os
        os.makedirs("tmp_scripts", exist_ok=True)
        output_path = "tmp_scripts/maps_business.json"
        with open(output_path, "w") as f:
            json.dump(result.model_dump(), f, indent=2, default=str)
        print(f"\nFull data saved to {output_path}")

    asyncio.run(_main())
