"""
Business Website Scraper

Scrapes the business's own website to extract branding, content, and media
that can be used to enhance the generated site. This runs AFTER the Google
Maps scraper and enriches the BusinessData with real website content.

Uses Playwright with the same persistent context pattern as the Maps scraper.
"""

import asyncio
import logging
import os
import re
from typing import Any, Optional
from urllib.parse import urljoin, urlparse

from pydantic import BaseModel, Field
from playwright.async_api import async_playwright, Page

logger = logging.getLogger(__name__)


class WebsiteData(BaseModel):
    """Data extracted from the business's own website."""

    url: str
    title: Optional[str] = None
    meta_description: Optional[str] = None
    logo_url: Optional[str] = None
    favicon_url: Optional[str] = None
    hero_image_url: Optional[str] = None
    brand_colors: list[str] = Field(default_factory=list, description="Hex colors found in CSS")
    headings: list[str] = Field(default_factory=list, description="Key headings from the page")
    about_text: Optional[str] = Field(default=None, description="About/mission text from the site")
    tagline: Optional[str] = None
    menu_items: list[dict[str, Any]] = Field(default_factory=list, description="Menu/product items if found")
    services: list[str] = Field(default_factory=list, description="Services listed on the site")
    social_links: dict[str, str] = Field(default_factory=dict, description="Social media URLs")
    images: list[str] = Field(default_factory=list, description="Key image URLs from the site")
    contact_info: dict[str, str] = Field(default_factory=dict, description="Email, phone, address from site")
    fonts: list[str] = Field(default_factory=list, description="Font families used on the site")


# JavaScript to extract website content
EXTRACT_WEBSITE_JS = """() => {
    const data = {};

    // Title
    data.title = document.title || '';

    // Meta description
    const metaDesc = document.querySelector('meta[name="description"]');
    if (metaDesc) data.meta_description = metaDesc.getAttribute('content');

    // OG description as fallback
    if (!data.meta_description) {
        const ogDesc = document.querySelector('meta[property="og:description"]');
        if (ogDesc) data.meta_description = ogDesc.getAttribute('content');
    }

    // Logo - try common selectors
    const logoSelectors = [
        'img[alt*="logo" i]', 'img[class*="logo" i]', 'img[id*="logo" i]',
        'a.logo img', '.logo img', '#logo img', 'header img:first-of-type',
        '[class*="brand"] img', 'a[href="/"] img',
    ];
    for (const sel of logoSelectors) {
        const logo = document.querySelector(sel);
        if (logo && logo.src) {
            data.logo_url = logo.src;
            break;
        }
    }

    // Favicon
    const favicon = document.querySelector('link[rel*="icon"]');
    if (favicon) data.favicon_url = favicon.href;

    // Hero image - large image in the top area
    const heroSelectors = [
        'section:first-of-type img[src]', '.hero img', '[class*="hero"] img',
        '[class*="banner"] img', 'header + * img', 'main > *:first-child img',
    ];
    for (const sel of heroSelectors) {
        const hero = document.querySelector(sel);
        if (hero && hero.src && hero.naturalWidth > 300) {
            data.hero_image_url = hero.src;
            break;
        }
    }

    // Key headings (h1, h2)
    const headings = [];
    document.querySelectorAll('h1, h2').forEach(h => {
        const text = h.innerText.trim();
        if (text && text.length > 2 && text.length < 200 && !headings.includes(text)) {
            headings.push(text);
        }
    });
    data.headings = headings.slice(0, 15);

    // Tagline - first h2 or subtitle-like element
    const taglineEl = document.querySelector('h2, [class*="tagline"], [class*="subtitle"], [class*="slogan"]');
    if (taglineEl) {
        const t = taglineEl.innerText.trim();
        if (t.length > 5 && t.length < 150) data.tagline = t;
    }

    // About text - look for about section or paragraphs
    const aboutSelectors = [
        '#about p', '.about p', '[class*="about"] p',
        '#story p', '.story p', '[class*="story"] p',
        '#mission p', '.mission p',
    ];
    for (const sel of aboutSelectors) {
        const els = document.querySelectorAll(sel);
        if (els.length > 0) {
            const texts = Array.from(els).map(e => e.innerText.trim()).filter(t => t.length > 20);
            if (texts.length > 0) {
                data.about_text = texts.join(' ').substring(0, 1000);
                break;
            }
        }
    }
    // Fallback: longest paragraph on the page
    if (!data.about_text) {
        let longest = '';
        document.querySelectorAll('p').forEach(p => {
            const t = p.innerText.trim();
            if (t.length > longest.length && t.length > 50 && t.length < 1000 &&
                !t.includes('cookie') && !t.includes('privacy') && !t.includes('©')) {
                longest = t;
            }
        });
        if (longest) data.about_text = longest;
    }

    // Menu/product items (for restaurants, shops, etc.)
    const menuItems = [];
    const menuSelectors = [
        '[class*="menu-item"], [class*="menu_item"], [class*="menuItem"]',
        '[class*="product"], [class*="dish"], [class*="food-item"]',
        '.menu li, #menu li, [class*="menu"] li',
    ];
    for (const sel of menuSelectors) {
        document.querySelectorAll(sel).forEach(el => {
            if (menuItems.length >= 20) return;
            const name = el.querySelector('h3, h4, .name, .title, strong');
            const price = el.querySelector('[class*="price"], .price');
            const desc = el.querySelector('p, .description, [class*="desc"]');
            if (name) {
                const item = {name: name.innerText.trim()};
                if (price) item.price = price.innerText.trim();
                if (desc) item.description = desc.innerText.trim().substring(0, 200);
                menuItems.push(item);
            }
        });
        if (menuItems.length > 0) break;
    }
    data.menu_items = menuItems;

    // Services
    const services = [];
    const serviceSelectors = [
        '[class*="service"] h3', '[class*="service"] h4',
        '#services li', '.services li', '[class*="service"] li',
        '[class*="offering"] h3', '[class*="offering"] h4',
    ];
    for (const sel of serviceSelectors) {
        document.querySelectorAll(sel).forEach(el => {
            const t = el.innerText.trim();
            if (t && t.length > 2 && t.length < 100) services.push(t);
        });
        if (services.length > 0) break;
    }
    data.services = services.slice(0, 15);

    // Social media links
    const socials = {};
    const socialPatterns = {
        facebook: /facebook\\.com/i,
        instagram: /instagram\\.com/i,
        twitter: /twitter\\.com|x\\.com/i,
        youtube: /youtube\\.com/i,
        tiktok: /tiktok\\.com/i,
        linkedin: /linkedin\\.com/i,
        yelp: /yelp\\.com/i,
    };
    document.querySelectorAll('a[href]').forEach(a => {
        const href = a.getAttribute('href') || '';
        for (const [name, pattern] of Object.entries(socialPatterns)) {
            if (pattern.test(href) && !socials[name]) {
                socials[name] = href;
            }
        }
    });
    data.social_links = socials;

    // Key images (larger than 200px, not icons)
    const images = [];
    const seenSrcs = new Set();
    document.querySelectorAll('img[src]').forEach(img => {
        const src = img.src;
        if (!src || src.startsWith('data:') || seenSrcs.has(src)) return;
        if (img.naturalWidth < 200 && img.width < 200) return;
        // Skip tiny icons, tracking pixels
        if (/favicon|icon|pixel|track|analytics|badge/i.test(src)) return;
        seenSrcs.add(src);
        images.push(src);
    });
    data.images = images.slice(0, 12);

    // Contact info
    const contact = {};
    // Email
    document.querySelectorAll('a[href^="mailto:"]').forEach(a => {
        if (!contact.email) contact.email = a.getAttribute('href').replace('mailto:', '');
    });
    // Phone
    document.querySelectorAll('a[href^="tel:"]').forEach(a => {
        if (!contact.phone) contact.phone = a.getAttribute('href').replace('tel:', '');
    });
    // Address
    const addrEl = document.querySelector('address, [class*="address"], [itemtype*="PostalAddress"]');
    if (addrEl) contact.address = addrEl.innerText.trim().substring(0, 200);
    data.contact_info = contact;

    // Fonts - extract from computed styles
    const fontSet = new Set();
    ['h1', 'h2', 'p', 'body'].forEach(tag => {
        const el = document.querySelector(tag);
        if (el) {
            const font = getComputedStyle(el).fontFamily;
            if (font) {
                // Extract first font name, clean quotes
                const primary = font.split(',')[0].replace(/['"]/g, '').trim();
                if (primary && !['serif', 'sans-serif', 'monospace', 'cursive'].includes(primary.toLowerCase())) {
                    fontSet.add(primary);
                }
            }
        }
    });
    data.fonts = Array.from(fontSet);

    return data;
}"""

# JavaScript to extract CSS custom properties and common colors
EXTRACT_COLORS_JS = """() => {
    const colors = new Set();

    // CSS custom properties (--primary, --brand, etc.)
    const root = getComputedStyle(document.documentElement);
    const rootStyles = document.documentElement.style;
    for (let i = 0; i < rootStyles.length; i++) {
        const prop = rootStyles[i];
        if (prop.startsWith('--')) {
            const val = root.getPropertyValue(prop).trim();
            if (/^#[0-9a-fA-F]{3,8}$/.test(val) || /^rgb/i.test(val)) {
                colors.add(val);
            }
        }
    }

    // Extract colors from key elements
    const elements = document.querySelectorAll(
        'header, nav, .hero, [class*="hero"], h1, h2, button, a.btn, [class*="btn"], footer'
    );
    elements.forEach(el => {
        const style = getComputedStyle(el);
        [style.color, style.backgroundColor, style.borderColor].forEach(c => {
            if (c && c !== 'rgba(0, 0, 0, 0)' && c !== 'transparent' && c !== 'rgb(0, 0, 0)' && c !== 'rgb(255, 255, 255)') {
                colors.add(c);
            }
        });
    });

    // Also check inline stylesheets for hex colors
    const sheets = document.styleSheets;
    try {
        for (const sheet of sheets) {
            try {
                for (const rule of sheet.cssRules || []) {
                    const text = rule.cssText || '';
                    const hexMatches = text.match(/#[0-9a-fA-F]{3,8}\\b/g);
                    if (hexMatches) {
                        hexMatches.forEach(h => {
                            // Skip common black/white/gray
                            if (!['#000', '#000000', '#fff', '#ffffff', '#333', '#666', '#999', '#ccc'].includes(h.toLowerCase())) {
                                colors.add(h);
                            }
                        });
                    }
                }
            } catch (e) { /* CORS stylesheet */ }
        }
    } catch (e) {}

    return Array.from(colors).slice(0, 20);
}"""


def _rgb_to_hex(rgb_str: str) -> str | None:
    """Convert 'rgb(r, g, b)' to '#rrggbb'."""
    m = re.match(r"rgba?\((\d+),\s*(\d+),\s*(\d+)", rgb_str)
    if m:
        r, g, b = int(m.group(1)), int(m.group(2)), int(m.group(3))
        return f"#{r:02x}{g:02x}{b:02x}"
    return None


async def scrape_website(url: str) -> WebsiteData:
    """
    Scrape a business website to extract branding, content, and media.

    Args:
        url: The business website URL to scrape.

    Returns:
        WebsiteData with extracted content.
    """
    if not url:
        return WebsiteData(url="")

    # Ensure URL has scheme
    if not url.startswith("http"):
        url = "https://" + url

    context = None
    async with async_playwright() as pw:
        try:
            profile_dir = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                ".chrome-profile",
            )
            has_display = bool(os.environ.get("DISPLAY"))

            context = await pw.chromium.launch_persistent_context(
                profile_dir,
                headless=not has_display,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--window-size=1920,1080",
                ],
                viewport={"width": 1920, "height": 1080},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/131.0.0.0 Safari/537.36"
                ),
                locale="en-US",
            )

            page = context.pages[0] if context.pages else await context.new_page()

            logger.info("Scraping website: %s", url)
            await page.goto(url, wait_until="load", timeout=30000)
            await asyncio.sleep(3)

            # Scroll down to trigger lazy-loaded images
            for _ in range(3):
                await page.evaluate("window.scrollBy(0, 800)")
                await asyncio.sleep(0.5)
            await page.evaluate("window.scrollTo(0, 0)")
            await asyncio.sleep(1)

            # Extract main content
            raw_data = await page.evaluate(EXTRACT_WEBSITE_JS)

            # Extract colors
            raw_colors = await page.evaluate(EXTRACT_COLORS_JS)

            # Convert rgb() colors to hex
            brand_colors: list[str] = []
            for c in raw_colors:
                if c.startswith("#"):
                    brand_colors.append(c)
                elif c.startswith("rgb"):
                    hex_val = _rgb_to_hex(c)
                    if hex_val:
                        brand_colors.append(hex_val)

            # Resolve relative URLs
            base_url = url
            for field in ["logo_url", "favicon_url", "hero_image_url"]:
                val = raw_data.get(field)
                if val and not val.startswith("http"):
                    raw_data[field] = urljoin(base_url, val)

            raw_data["images"] = [
                urljoin(base_url, img) if not img.startswith("http") else img
                for img in (raw_data.get("images") or [])
            ]

            website = WebsiteData(
                url=url,
                title=raw_data.get("title"),
                meta_description=raw_data.get("meta_description"),
                logo_url=raw_data.get("logo_url"),
                favicon_url=raw_data.get("favicon_url"),
                hero_image_url=raw_data.get("hero_image_url"),
                brand_colors=brand_colors,
                headings=raw_data.get("headings", []),
                about_text=raw_data.get("about_text"),
                tagline=raw_data.get("tagline"),
                menu_items=raw_data.get("menu_items", []),
                services=raw_data.get("services", []),
                social_links=raw_data.get("social_links", {}),
                images=raw_data.get("images", []),
                contact_info=raw_data.get("contact_info", {}),
                fonts=raw_data.get("fonts", []),
            )

            logger.info(
                "Website scrape complete: %d images, %d headings, %d colors, %d social links",
                len(website.images),
                len(website.headings),
                len(website.brand_colors),
                len(website.social_links),
            )

            return website

        except Exception as exc:
            logger.warning("Website scraping failed (non-fatal): %s", exc)
            return WebsiteData(url=url)

        finally:
            if context:
                await context.close()


if __name__ == "__main__":
    import json

    async def _main() -> None:
        import sys

        url = sys.argv[1] if len(sys.argv) > 1 else "https://www.tkilaaldie.com/"
        print(f"Scraping website: {url}")

        result = await scrape_website(url)

        print(f"\n{'=' * 60}")
        print(f"Title: {result.title}")
        print(f"Description: {result.meta_description}")
        print(f"Tagline: {result.tagline}")
        print(f"Logo: {result.logo_url}")
        print(f"Hero image: {result.hero_image_url}")
        print(f"Colors: {result.brand_colors[:8]}")
        print(f"Fonts: {result.fonts}")
        print(f"Headings: {result.headings[:8]}")
        print(f"About: {(result.about_text or 'N/A')[:200]}")
        print(f"Social: {result.social_links}")
        print(f"Contact: {result.contact_info}")
        print(f"Images: {len(result.images)}")
        print(f"Menu items: {len(result.menu_items)}")
        print(f"Services: {result.services[:5]}")

        if result.menu_items:
            print("\nMenu items:")
            for item in result.menu_items[:8]:
                name = item.get("name", "?")
                price = item.get("price", "")
                print(f"  {name} {price}")

        if result.images:
            print("\nImages:")
            for img in result.images[:5]:
                print(f"  {img[:90]}...")

    asyncio.run(_main())
