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
    hours: Optional[dict[str, str]] = Field(default=None, description="Business hours by day")
    subpages_scraped: list[str] = Field(default_factory=list, description="Subpage URLs visited beyond homepage")
    nav_structure: list[dict[str, str]] = Field(default_factory=list, description="Navigation menu items {label, url}")
    all_locations: list[str] = Field(default_factory=list, description="All street addresses found (multi-location businesses)")
    contact_confidence: str = Field(default="none", description="Confidence in contact info: 'high' (1 location), 'low' (multi-location/franchise), 'none' (no data)")
    is_franchise: bool = Field(default=False, description="Whether the site appears to be a franchise/multi-location business")


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

    // Contact info — deep extraction
    const contact = {};

    // Email: try mailto links first, then regex scan body text
    document.querySelectorAll('a[href^="mailto:"]').forEach(a => {
        if (!contact.email) contact.email = a.getAttribute('href').replace('mailto:', '').split('?')[0];
    });
    if (!contact.email) {
        const emailMatch = document.body.innerText.match(/[a-zA-Z0-9._%+\\-]+@[a-zA-Z0-9.\\-]+\\.[a-zA-Z]{2,}/);
        if (emailMatch) contact.email = emailMatch[0];
    }

    // Phone: try tel links first, then regex scan body text for US formats
    document.querySelectorAll('a[href^="tel:"]').forEach(a => {
        if (!contact.phone) contact.phone = a.getAttribute('href').replace('tel:', '');
    });
    if (!contact.phone) {
        const phoneMatch = document.body.innerText.match(/(?:\\+1[\\s.-]?)?\\(?\\d{3}\\)?[\\s.-]?\\d{3}[\\s.-]?\\d{4}/);
        if (phoneMatch) contact.phone = phoneMatch[0].trim();
    }

    // Address: use regex pattern matching to find real street addresses
    const addrRegex = /\\d{1,5}\\s+(?:[A-Za-z0-9.]+\\s+){0,4}(?:Street|St|Avenue|Ave|Boulevard|Blvd|Drive|Dr|Road|Rd|Lane|Ln|Way|Court|Ct|Place|Pl|Parkway|Pkwy|Highway|Hwy|Circle|Trail|Terrace|Broadway)(?:[,\\s]+[A-Z][a-z]{2,}(?:\\s+[A-Z][a-z]{2,})?)?(?:[,\\s]+[A-Z]{2})?(?:\\s+\\d{5}(?:-\\d{4})?)?/g;

    // Try structured address elements first (but validate content looks like an address)
    const addrSelectors = ['address', '[itemtype*="PostalAddress"]', '[class*="address"]'];
    for (const sel of addrSelectors) {
        const el = document.querySelector(sel);
        if (el) {
            const txt = el.innerText.trim();
            const addrInEl = txt.match(addrRegex);
            if (addrInEl) { contact.address = addrInEl[0].trim(); break; }
        }
    }
    // Try footer text
    if (!contact.address) {
        const footer = document.querySelector('footer');
        if (footer) {
            const addrMatch = footer.innerText.match(addrRegex);
            if (addrMatch) contact.address = addrMatch[0].trim();
        }
    }
    // Try full body text as last resort
    if (!contact.address) {
        const bodyMatch = document.body.innerText.match(addrRegex);
        if (bodyMatch) contact.address = bodyMatch[0].trim();
    }

    // Multi-location detection: find all addresses on the page
    const allAddresses = [];
    const bodyMatches = document.body.innerText.match(addrRegex) || [];
    const seenAddrs = new Set();
    for (const m of bodyMatches) {
        const clean = m.trim();
        if (clean.length > 10 && !seenAddrs.has(clean)) {
            seenAddrs.add(clean);
            allAddresses.push(clean);
        }
    }
    if (allAddresses.length > 1) data.all_locations = allAddresses;

    // Franchise detection signals
    let franchiseSignals = 0;
    // Check nav items for location-finder patterns
    const navText = Array.from(document.querySelectorAll('nav a, header a')).map(a => a.innerText.toLowerCase()).join(' ');
    if (/locations?|find a store|store locator|find us|our stores/i.test(navText)) franchiseSignals++;
    // Check for store locator iframes or widgets
    if (document.querySelector('iframe[src*="store"], iframe[src*="location"], [class*="store-locator"], [class*="storelocator"], [id*="store-locator"]')) franchiseSignals++;
    // Multiple phone numbers in body
    const phoneMatches = document.body.innerText.match(/(?:\\+1[\\s.-]?)?\\(?\\d{3}\\)?[\\s.-]?\\d{3}[\\s.-]?\\d{4}/g) || [];
    if (phoneMatches.length > 2) franchiseSignals++;
    // Multiple addresses detected
    if (allAddresses.length > 1) franchiseSignals++;
    data.franchise_signals = franchiseSignals;
    data.contact_info = contact;

    // JSON-LD structured data
    const jsonLdData = {};
    document.querySelectorAll('script[type="application/ld+json"]').forEach(script => {
        try {
            let parsed = JSON.parse(script.textContent);
            // Handle @graph arrays
            if (parsed['@graph']) parsed = parsed['@graph'];
            const items = Array.isArray(parsed) ? parsed : [parsed];
            for (const item of items) {
                const t = (item['@type'] || '').toLowerCase();
                if (['localbusiness', 'restaurant', 'organization', 'store',
                     'foodestablishment', 'barorcafe', 'bakery', 'cafeorrestaurant'].some(k => t.includes(k))) {
                    if (item.telephone) jsonLdData.telephone = item.telephone;
                    if (item.email) jsonLdData.email = item.email;
                    if (item.address) {
                        const a = item.address;
                        const parts = [a.streetAddress, a.addressLocality, a.addressRegion, a.postalCode].filter(Boolean);
                        if (parts.length > 0) jsonLdData.address = parts.join(', ');
                    }
                    if (item.openingHoursSpecification) jsonLdData.openingHoursSpecification = item.openingHoursSpecification;
                    if (item.name) jsonLdData.name = item.name;
                    if (item.description) jsonLdData.description = item.description;
                    if (item.priceRange) jsonLdData.priceRange = item.priceRange;
                    if (item.servesCuisine) jsonLdData.servesCuisine = item.servesCuisine;
                    if (item.aggregateRating) jsonLdData.aggregateRating = item.aggregateRating;
                }
            }
        } catch (e) {}
    });
    data.json_ld = Object.keys(jsonLdData).length > 0 ? jsonLdData : null;

    // Fill contact gaps from JSON-LD
    if (jsonLdData.telephone && !contact.phone) contact.phone = jsonLdData.telephone;
    if (jsonLdData.email && !contact.email) contact.email = jsonLdData.email;
    if (jsonLdData.address && !contact.address) contact.address = jsonLdData.address;

    // Business hours
    const hours = {};
    const dayNames = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'];

    // From JSON-LD openingHoursSpecification
    if (jsonLdData.openingHoursSpecification) {
        const specs = Array.isArray(jsonLdData.openingHoursSpecification) ? jsonLdData.openingHoursSpecification : [jsonLdData.openingHoursSpecification];
        for (const spec of specs) {
            const days = Array.isArray(spec.dayOfWeek) ? spec.dayOfWeek : [spec.dayOfWeek];
            for (let day of days) {
                if (!day) continue;
                day = day.replace('https://schema.org/', '').replace('http://schema.org/', '');
                if (spec.opens && spec.closes) hours[day] = spec.opens + ' - ' + spec.closes;
            }
        }
    }

    // Schema.org itemprop
    if (Object.keys(hours).length === 0) {
        document.querySelectorAll('[itemprop="openingHoursSpecification"]').forEach(el => {
            const day = el.querySelector('[itemprop="dayOfWeek"]');
            const opens = el.querySelector('[itemprop="opens"]');
            const closes = el.querySelector('[itemprop="closes"]');
            if (day && opens && closes) {
                hours[day.textContent.trim()] = opens.textContent.trim() + ' - ' + closes.textContent.trim();
            }
        });
    }

    // CSS class matching
    if (Object.keys(hours).length === 0) {
        const hourEls = document.querySelectorAll('[class*="hour"], [class*="schedule"], [class*="opening"]');
        hourEls.forEach(el => {
            const text = el.innerText.trim();
            for (const day of dayNames) {
                const re = new RegExp(day + '[:\\\\s]+([\\\\d:]+\\\\s*(?:AM|PM)?\\\\s*-\\\\s*[\\\\d:]+\\\\s*(?:AM|PM)?)', 'i');
                const m = text.match(re);
                if (m) hours[day] = m[1].trim();
            }
        });
    }

    // Regex scan of body text as last resort
    if (Object.keys(hours).length === 0) {
        const bodyText = document.body.innerText;
        for (const day of dayNames) {
            const re = new RegExp(day + '[:\\\\s]+([\\\\d:]+\\\\s*(?:AM|PM)?\\\\s*[-–]\\\\s*[\\\\d:]+\\\\s*(?:AM|PM)?)', 'i');
            const m = bodyText.match(re);
            if (m) hours[day] = m[1].trim();
        }
    }
    data.hours = Object.keys(hours).length > 0 ? hours : null;

    // Navigation structure
    const navItems = [];
    const navSeen = new Set();
    document.querySelectorAll('nav a[href], header a[href]').forEach(a => {
        const label = a.innerText.trim();
        const href = a.getAttribute('href') || '';
        if (label && label.length > 0 && label.length < 60 && href && !navSeen.has(href)) {
            navSeen.add(href);
            navItems.push({label: label, url: href});
        }
    });
    data.nav_items = navItems;

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


# JavaScript to extract same-host internal links for subpage crawling
EXTRACT_NAV_LINKS_JS = """(baseHost) => {
    const links = new Set();
    const skipExtensions = /\\.(pdf|zip|doc|docx|xls|xlsx|ppt|pptx|jpg|jpeg|png|gif|svg|webp|mp4|mp3|avi|mov)$/i;
    const skipPaths = /\\/(cart|checkout|account|login|signup|register|password|admin|wp-admin|wp-login|feed|rss|api|search|tag|author|category|page\\/\\d)\\b/i;
    document.querySelectorAll('a[href]').forEach(a => {
        try {
            const url = new URL(a.href, window.location.origin);
            if (url.hostname !== baseHost) return;
            if (url.hash && url.pathname === window.location.pathname) return;
            if (/^javascript:/i.test(a.getAttribute('href'))) return;
            if (/^mailto:/i.test(a.getAttribute('href'))) return;
            if (/^tel:/i.test(a.getAttribute('href'))) return;
            if (skipExtensions.test(url.pathname)) return;
            if (skipPaths.test(url.pathname)) return;
            const normalized = url.origin + url.pathname.replace(/\\/$/, '');
            if (normalized === window.location.origin + window.location.pathname.replace(/\\/$/, '')) return;
            links.add(normalized);
        } catch (e) {}
    });
    return Array.from(links);
}"""

# JavaScript for lighter subpage extraction (no logo/favicon/hero/colors/fonts)
EXTRACT_SUBPAGE_JS = """() => {
    const data = {};

    // Contact info — same deep extraction as homepage
    const contact = {};
    document.querySelectorAll('a[href^="mailto:"]').forEach(a => {
        if (!contact.email) contact.email = a.getAttribute('href').replace('mailto:', '').split('?')[0];
    });
    if (!contact.email) {
        const emailMatch = document.body.innerText.match(/[a-zA-Z0-9._%+\\-]+@[a-zA-Z0-9.\\-]+\\.[a-zA-Z]{2,}/);
        if (emailMatch) contact.email = emailMatch[0];
    }
    document.querySelectorAll('a[href^="tel:"]').forEach(a => {
        if (!contact.phone) contact.phone = a.getAttribute('href').replace('tel:', '');
    });
    if (!contact.phone) {
        const phoneMatch = document.body.innerText.match(/(?:\\+1[\\s.-]?)?\\(?\\d{3}\\)?[\\s.-]?\\d{3}[\\s.-]?\\d{4}/);
        if (phoneMatch) contact.phone = phoneMatch[0].trim();
    }
    const addrRegex = /\\d{1,5}\\s+(?:[A-Za-z0-9.]+\\s+){0,4}(?:Street|St|Avenue|Ave|Boulevard|Blvd|Drive|Dr|Road|Rd|Lane|Ln|Way|Court|Ct|Place|Pl|Parkway|Pkwy|Highway|Hwy|Circle|Trail|Terrace|Broadway)(?:[,\\s]+[A-Z][a-z]{2,}(?:\\s+[A-Z][a-z]{2,})?)?(?:[,\\s]+[A-Z]{2})?(?:\\s+\\d{5}(?:-\\d{4})?)?/g;
    const addrSelectors = ['address', '[itemtype*="PostalAddress"]', '[class*="address"]'];
    for (const sel of addrSelectors) {
        const el = document.querySelector(sel);
        if (el) {
            const addrInEl = el.innerText.trim().match(addrRegex);
            if (addrInEl) { contact.address = addrInEl[0].trim(); break; }
        }
    }
    if (!contact.address) {
        const footer = document.querySelector('footer');
        if (footer) {
            const addrMatch = footer.innerText.match(addrRegex);
            if (addrMatch) contact.address = addrMatch[0].trim();
        }
    }
    data.contact_info = contact;

    // JSON-LD structured data
    const jsonLdData = {};
    document.querySelectorAll('script[type="application/ld+json"]').forEach(script => {
        try {
            let parsed = JSON.parse(script.textContent);
            if (parsed['@graph']) parsed = parsed['@graph'];
            const items = Array.isArray(parsed) ? parsed : [parsed];
            for (const item of items) {
                const t = (item['@type'] || '').toLowerCase();
                if (['localbusiness', 'restaurant', 'organization', 'store',
                     'foodestablishment', 'barorcafe', 'bakery', 'cafeorrestaurant'].some(k => t.includes(k))) {
                    if (item.telephone) jsonLdData.telephone = item.telephone;
                    if (item.email) jsonLdData.email = item.email;
                    if (item.address) {
                        const a = item.address;
                        const parts = [a.streetAddress, a.addressLocality, a.addressRegion, a.postalCode].filter(Boolean);
                        if (parts.length > 0) jsonLdData.address = parts.join(', ');
                    }
                    if (item.openingHoursSpecification) jsonLdData.openingHoursSpecification = item.openingHoursSpecification;
                }
            }
        } catch (e) {}
    });
    if (jsonLdData.telephone && !contact.phone) contact.phone = jsonLdData.telephone;
    if (jsonLdData.email && !contact.email) contact.email = jsonLdData.email;
    if (jsonLdData.address && !contact.address) contact.address = jsonLdData.address;

    // Hours
    const hours = {};
    const dayNames = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'];
    if (jsonLdData.openingHoursSpecification) {
        const specs = Array.isArray(jsonLdData.openingHoursSpecification) ? jsonLdData.openingHoursSpecification : [jsonLdData.openingHoursSpecification];
        for (const spec of specs) {
            const days = Array.isArray(spec.dayOfWeek) ? spec.dayOfWeek : [spec.dayOfWeek];
            for (let day of days) {
                if (!day) continue;
                day = day.replace('https://schema.org/', '').replace('http://schema.org/', '');
                if (spec.opens && spec.closes) hours[day] = spec.opens + ' - ' + spec.closes;
            }
        }
    }
    if (Object.keys(hours).length === 0) {
        document.querySelectorAll('[itemprop="openingHoursSpecification"]').forEach(el => {
            const day = el.querySelector('[itemprop="dayOfWeek"]');
            const opens = el.querySelector('[itemprop="opens"]');
            const closes = el.querySelector('[itemprop="closes"]');
            if (day && opens && closes) hours[day.textContent.trim()] = opens.textContent.trim() + ' - ' + closes.textContent.trim();
        });
    }
    if (Object.keys(hours).length === 0) {
        document.querySelectorAll('[class*="hour"], [class*="schedule"], [class*="opening"]').forEach(el => {
            const text = el.innerText.trim();
            for (const day of dayNames) {
                const re = new RegExp(day + '[:\\\\s]+([\\\\d:]+\\\\s*(?:AM|PM)?\\\\s*-\\\\s*[\\\\d:]+\\\\s*(?:AM|PM)?)', 'i');
                const m = text.match(re);
                if (m) hours[day] = m[1].trim();
            }
        });
    }
    if (Object.keys(hours).length === 0) {
        const bodyText = document.body.innerText;
        for (const day of dayNames) {
            const re = new RegExp(day + '[:\\\\s]+([\\\\d:]+\\\\s*(?:AM|PM)?\\\\s*[-\\u2013]\\\\s*[\\\\d:]+\\\\s*(?:AM|PM)?)', 'i');
            const m = bodyText.match(re);
            if (m) hours[day] = m[1].trim();
        }
    }
    data.hours = Object.keys(hours).length > 0 ? hours : null;

    // Social links
    const socials = {};
    const socialPatterns = {
        facebook: /facebook\\.com/i, instagram: /instagram\\.com/i,
        twitter: /twitter\\.com|x\\.com/i, youtube: /youtube\\.com/i,
        tiktok: /tiktok\\.com/i, linkedin: /linkedin\\.com/i, yelp: /yelp\\.com/i,
    };
    document.querySelectorAll('a[href]').forEach(a => {
        const href = a.getAttribute('href') || '';
        for (const [name, pattern] of Object.entries(socialPatterns)) {
            if (pattern.test(href) && !socials[name]) socials[name] = href;
        }
    });
    data.social_links = socials;

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

    // About text
    const aboutSelectors = [
        '[class*="about"] p', '[class*="story"] p',
        '#about p', '.about p', '#story p', '.story p', '#mission p', '.mission p',
    ];
    for (const sel of aboutSelectors) {
        const els = document.querySelectorAll(sel);
        if (els.length > 0) {
            const texts = Array.from(els).map(e => e.innerText.trim()).filter(t => t.length > 20);
            if (texts.length > 0) { data.about_text = texts.join(' ').substring(0, 1000); break; }
        }
    }

    // Images (> 200px, skip icons, cap at 8)
    const images = [];
    const seenSrcs = new Set();
    document.querySelectorAll('img[src]').forEach(img => {
        const src = img.src;
        if (!src || src.startsWith('data:') || seenSrcs.has(src)) return;
        if (img.naturalWidth < 200 && img.width < 200) return;
        if (/favicon|icon|pixel|track|analytics|badge/i.test(src)) return;
        seenSrcs.add(src);
        images.push(src);
    });
    data.images = images.slice(0, 8);

    // Multi-location detection on subpages too
    const addrRegex2 = /\\d{1,5}\\s+(?:[A-Za-z0-9.]+\\s+){0,4}(?:Street|St|Avenue|Ave|Boulevard|Blvd|Drive|Dr|Road|Rd|Lane|Ln|Way|Court|Ct|Place|Pl|Parkway|Pkwy|Highway|Hwy|Circle|Trail|Terrace|Broadway)(?:[,\\s]+[A-Z][a-z]{2,}(?:\\s+[A-Z][a-z]{2,})?)?(?:[,\\s]+[A-Z]{2})?(?:\\s+\\d{5}(?:-\\d{4})?)?/g;
    const subpageAddresses = [];
    const bodyAddrMatches = document.body.innerText.match(addrRegex2) || [];
    const seenSubAddrs = new Set();
    for (const m of bodyAddrMatches) {
        const clean = m.trim();
        if (clean.length > 10 && !seenSubAddrs.has(clean)) {
            seenSubAddrs.add(clean);
            subpageAddresses.push(clean);
        }
    }
    if (subpageAddresses.length > 0) data.all_locations = subpageAddresses;

    return data;
}"""


def _rgb_to_hex(rgb_str: str) -> str | None:
    """Convert 'rgb(r, g, b)' to '#rrggbb'."""
    m = re.match(r"rgba?\((\d+),\s*(\d+),\s*(\d+)", rgb_str)
    if m:
        r, g, b = int(m.group(1)), int(m.group(2)), int(m.group(3))
        return f"#{r:02x}{g:02x}{b:02x}"
    return None


async def _scrape_page(page: Page, url: str) -> None:
    """Navigate to URL and scroll to trigger lazy loading."""
    await page.goto(url, wait_until="load", timeout=20000)
    await asyncio.sleep(2)
    for _ in range(3):
        await page.evaluate("window.scrollBy(0, 800)")
        await asyncio.sleep(0.3)
    await page.evaluate("window.scrollTo(0, 0)")
    await asyncio.sleep(0.5)


def _merge_subpage_data(website: WebsiteData, subpage_data: dict) -> None:
    """Merge data from a subpage into main WebsiteData. Fill gaps only."""
    # Contact — fill missing fields only
    sub_contact = subpage_data.get("contact_info", {})
    if sub_contact.get("email") and not website.contact_info.get("email"):
        website.contact_info["email"] = sub_contact["email"]
    if sub_contact.get("phone") and not website.contact_info.get("phone"):
        website.contact_info["phone"] = sub_contact["phone"]
    if sub_contact.get("address") and not website.contact_info.get("address"):
        website.contact_info["address"] = sub_contact["address"]

    # Hours — only if missing
    if subpage_data.get("hours") and not website.hours:
        website.hours = subpage_data["hours"]

    # Social links — fill gaps
    for platform, link in subpage_data.get("social_links", {}).items():
        if platform not in website.social_links:
            website.social_links[platform] = link

    # Services — append unique
    existing = set(website.services)
    for svc in subpage_data.get("services", []):
        if svc not in existing:
            website.services.append(svc)
            existing.add(svc)

    # About text — use if longer and we don't have one
    sub_about = subpage_data.get("about_text")
    if sub_about and (not website.about_text or len(sub_about) > len(website.about_text)):
        website.about_text = sub_about

    # Images — append unique, cap at 20
    existing_imgs = set(website.images)
    for img in subpage_data.get("images", []):
        if img not in existing_imgs and len(website.images) < 20:
            website.images.append(img)
            existing_imgs.add(img)

    # Merge discovered locations from subpages
    sub_locations = subpage_data.get("all_locations", [])
    existing_locs = set(website.all_locations)
    for loc in sub_locations:
        if loc not in existing_locs:
            website.all_locations.append(loc)
            existing_locs.add(loc)


async def scrape_website(url: str, max_subpages: int = 10) -> WebsiteData:
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
                hours=raw_data.get("hours"),
                nav_structure=raw_data.get("nav_items", []),
                all_locations=raw_data.get("all_locations", []),
            )

            # --- Subpage crawling ---
            base_host = urlparse(url).hostname
            all_internal_links: list[str] = []
            try:
                all_internal_links = await page.evaluate(EXTRACT_NAV_LINKS_JS, base_host)
            except Exception as exc:
                logger.debug("Failed to extract internal links: %s", exc)

            # Priority sort: contact/about/services pages first
            priority_high = re.compile(r"contact|about|services|menu|hours|location", re.IGNORECASE)
            priority_mid = re.compile(r"gallery|team|faq|testimonial|portfolio|pricing", re.IGNORECASE)

            def _link_priority(link: str) -> int:
                if priority_high.search(link):
                    return 0
                if priority_mid.search(link):
                    return 1
                return 2

            all_internal_links.sort(key=_link_priority)

            # Normalize homepage URL for dedup
            homepage_normalized = urlparse(url)._replace(fragment="").geturl().rstrip("/")
            visited = {homepage_normalized}
            subpages_visited: list[str] = []

            for link in all_internal_links:
                if len(subpages_visited) >= max_subpages:
                    break
                normalized = link.rstrip("/")
                if normalized in visited:
                    continue
                visited.add(normalized)
                try:
                    await _scrape_page(page, link)
                    subpage_data = await page.evaluate(EXTRACT_SUBPAGE_JS)
                    _merge_subpage_data(website, subpage_data)
                    subpages_visited.append(link)
                    logger.debug("Scraped subpage: %s", link)
                except Exception as exc:
                    logger.debug("Skipping subpage %s: %s", link, exc)

            website.subpages_scraped = subpages_visited

            # Compute contact confidence
            location_count = len(website.all_locations)
            franchise_signals = raw_data.get("franchise_signals", 0)
            if location_count == 1 and franchise_signals < 2:
                website.contact_confidence = "high"
            elif location_count == 0:
                website.contact_confidence = "none" if not website.contact_info.get("address") else "high"
            else:
                website.contact_confidence = "low"
                website.is_franchise = True

            logger.info(
                "Website scrape complete: %d images, %d headings, %d colors, %d social links, "
                "%d subpages | phone=%s email=%s address=%s hours=%s confidence=%s franchise=%s",
                len(website.images),
                len(website.headings),
                len(website.brand_colors),
                len(website.social_links),
                len(subpages_visited),
                bool(website.contact_info.get("phone")),
                bool(website.contact_info.get("email")),
                bool(website.contact_info.get("address")),
                bool(website.hours),
                website.contact_confidence,
                website.is_franchise,
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
        print(f"Hours: {result.hours}")
        if result.all_locations:
            print(f"All locations ({len(result.all_locations)}):")
            for loc in result.all_locations:
                print(f"  - {loc}")
        print(f"Contact confidence: {result.contact_confidence}")
        print(f"Is franchise: {result.is_franchise}")
        print(f"Nav items: {len(result.nav_structure)}")
        print(f"Subpages scraped: {len(result.subpages_scraped)}")
        for sp in result.subpages_scraped:
            print(f"  {sp}")
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
