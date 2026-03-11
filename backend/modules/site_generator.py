"""
Site Generator Module

Generates website content from scraped business data using Claude API,
then renders it into a complete, standalone HTML page. Orchestrates the
full pipeline: business data -> AI content generation -> HTML rendering.

Integration Points:
- Called by the site builder service/router
- Uses anthropic SDK for Claude API calls
- Produces self-contained HTML with TailwindCSS + Google Fonts via CDN
"""

import json
import os
import re
from pathlib import Path
from typing import Any, Callable, Coroutine, Optional

import anthropic
from pydantic import BaseModel, Field


def _get_anthropic_client() -> anthropic.AsyncAnthropic:
    """Create an Anthropic client using the best available credentials.

    Priority:
    1. ANTHROPIC_API_KEY environment variable
    2. Claude Code OAuth token from ~/.claude/.credentials.json
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        return anthropic.AsyncAnthropic(api_key=api_key)

    # Try Claude Code OAuth token
    creds_path = Path.home() / ".claude" / ".credentials.json"
    if creds_path.exists():
        creds = json.loads(creds_path.read_text())
        oauth = creds.get("claudeAiOauth", {})
        access_token = oauth.get("accessToken")
        if access_token:
            return anthropic.AsyncAnthropic(auth_token=access_token)

    raise ValueError(
        "No Anthropic credentials found. Set ANTHROPIC_API_KEY env var "
        "or ensure Claude Code OAuth token exists at ~/.claude/.credentials.json"
    )


# ═══════════════════════════════════════════════════════════
# PYDANTIC MODELS
# ═══════════════════════════════════════════════════════════


class SiteContent(BaseModel):
    """AI-generated website content and design tokens.

    Holds all the text, color, and typography choices that Claude
    produces from scraped business data. Each field maps to a
    specific section or design decision in the final HTML output.
    """

    # Hero
    hero_headline: str = Field(
        ..., description="Primary headline for the hero/banner section"
    )
    hero_subheadline: str = Field(
        ..., description="Supporting text below the hero headline"
    )
    # About
    about_title: str = Field(
        ..., description="Heading for the About section"
    )
    about_text: str = Field(
        ..., description="Body copy for the About section (2-3 paragraphs)"
    )
    # Services
    services: list[dict] = Field(
        default_factory=list,
        description="List of services with: name, description, icon_suggestion",
    )
    # Why Choose Us
    why_choose_us: list[dict] = Field(
        default_factory=list,
        description="3-4 differentiators with: title, description, icon_key",
    )
    # Process / How It Works
    process_steps: list[dict] = Field(
        default_factory=list,
        description="3-4 steps with: step_number, title, description, icon_key",
    )
    # Testimonials
    testimonials: list[dict] = Field(
        default_factory=list,
        description="List of testimonials with: author, rating, text",
    )
    # FAQ
    faq_items: list[dict] = Field(
        default_factory=list,
        description="5-6 FAQ items with: question, answer",
    )
    # CTA
    cta_headline: str = Field(
        ..., description="Headline for the call-to-action section"
    )
    cta_button_text: str = Field(
        ..., description="Text for the primary CTA button"
    )
    # SEO
    seo_title: str = Field(
        ..., description="SEO-optimized page title (<title> tag)"
    )
    seo_description: str = Field(
        ..., description="SEO meta description (150-160 chars ideal)"
    )
    og_title: str = Field(
        default="", description="Open Graph title for social sharing"
    )
    og_description: str = Field(
        default="", description="Open Graph description for social sharing"
    )
    # Social proof
    tagline: str = Field(
        default="", description="Short tagline for the social proof bar"
    )
    # Design tokens
    color_primary: str = Field(
        ..., description="Primary brand color as hex (e.g. #2563EB)"
    )
    color_secondary: str = Field(
        ..., description="Secondary/accent color as hex (e.g. #F59E0B)"
    )
    font_heading: str = Field(
        ..., description="Google Font name for headings (e.g. Montserrat)"
    )
    font_body: str = Field(
        ..., description="Google Font name for body text (e.g. Open Sans)"
    )
    # Unsplash image keywords for sections without real photos
    hero_image_keyword: str = Field(
        default="", description="Unsplash keyword for hero background if no photos"
    )


class DeployResult(BaseModel):
    """Result of deploying a site to a hosting provider."""

    provider: str = Field(..., description="Hosting provider: vercel, cloudflare, none")
    url: Optional[str] = Field(default=None, description="Live deployment URL")
    deployment_id: Optional[str] = Field(default=None, description="Provider deployment ID")
    project_name: Optional[str] = Field(default=None, description="Project name on provider")
    error: Optional[str] = Field(default=None, description="Error message if deployment failed")


class GeneratedSite(BaseModel):
    """Complete generated site output: content + rendered HTML.

    Returned by the top-level generate_site() orchestrator function.
    Contains the business name, structured content, final HTML string,
    and the template name that was used for rendering.
    """

    business_name: str = Field(
        ..., description="Name of the business this site was generated for"
    )
    content: SiteContent = Field(
        ..., description="Structured AI-generated content"
    )
    html: str = Field(
        ..., description="Complete rendered HTML string (standalone page)"
    )
    template_name: str = Field(
        ..., description="Name of the template used for rendering"
    )
    dist_path: Optional[str] = Field(
        default=None, description="Path to built React dist/ directory"
    )
    build_dir: Optional[str] = Field(
        default=None, description="Path to temp build directory"
    )
    deploy: Optional[DeployResult] = Field(
        default=None, description="Deployment result if auto-deployed"
    )


# ═══════════════════════════════════════════════════════════
# CONTENT GENERATION (Claude API)
# ═══════════════════════════════════════════════════════════

# Type alias for the optional async progress callback
ProgressCallback = Optional[Callable[[str], Coroutine[Any, Any, None]]]

CONTENT_GENERATION_SYSTEM_PROMPT = """\
You are an elite website copywriter and brand designer who creates premium, \
client-ready business websites that sell for $500-$800. Given business data \
scraped from Google Maps, you produce compelling, conversion-optimized website \
copy and sophisticated design choices.

RULES:
- Write in a confident, premium tone appropriate to the business industry.
- Headlines should be benefit-driven and emotionally compelling (not generic).
- About text should be 2-3 substantial paragraphs that tell the business story.
- Adapt section names to fit the business type. For restaurants/bars use menu \
highlights or specialties instead of "services". For retail use product categories. \
For service businesses use actual services offered.
- Each service/offering should have a name, a 2-sentence description, and an icon name \
from this set: wrench, heart, shield-check, chart-bar, clock, map-pin, star, \
truck, camera, paint-brush, cog, bolt, scale, document-text, calculator, \
academic-cap, briefcase, globe, users, sparkles, fire, cube, scissors, \
musical-note, wifi, key, sun, phone, home, check-circle.
- Include 3-4 "Why Choose Us" differentiators with icon_key from the same set.
- "How It Works" process steps: ONLY include these for service-based businesses \
(contractors, agencies, consultants, salons, etc.) where a customer journey makes \
sense. Do NOT include process_steps for restaurants, bars, retail shops, or venues — \
set process_steps to an empty array [] for these.
- Include 5-6 FAQ items with real answers relevant to the business type.
- Testimonials: If real customer reviews are provided, use them VERBATIM as \
testimonials (exact author name, exact text, exact rating). Do NOT rewrite or \
fabricate reviews. If no reviews are provided, create realistic sample \
testimonials with "[Sample]" prefix on the author name.
- Choose a sophisticated color palette: primary should be bold but professional, \
secondary should complement it. Avoid generic blue unless it fits the brand.
- Choose premium Google Font pairings (e.g., Playfair Display + Inter, \
Montserrat + Lato, Raleway + Open Sans, Poppins + Source Sans Pro).
- Include a short tagline for the social proof bar.
- Suggest an Unsplash keyword for hero background if no business photos exist.
- SEO title under 60 chars, include city/location if available for local SEO.
- Meta description 150-160 chars, include business type + location for local search.
- OG title/description optimized for social media sharing.
- Include location-specific keywords naturally in hero_headline and about_text \
for local search ranking (e.g., "best [category] in [city]").

You MUST respond with a single JSON object (no markdown fences, no preamble):

{
  "hero_headline": "string (benefit-driven, emotionally compelling)",
  "hero_subheadline": "string (supporting value proposition)",
  "about_title": "string",
  "about_text": "string (2-3 paragraphs)",
  "services": [
    {"name": "string", "description": "string (2 sentences)", "icon_suggestion": "icon-name"}
  ],
  "why_choose_us": [
    {"title": "string", "description": "string", "icon_key": "icon-name"}
  ],
  "process_steps": [
    {"step_number": 1, "title": "string", "description": "string", "icon_key": "icon-name"}
  ],
  "testimonials": [
    {"author": "string", "rating": 5, "text": "string"}
  ],
  "faq_items": [
    {"question": "string", "answer": "string"}
  ],
  "cta_headline": "string",
  "cta_button_text": "string",
  "tagline": "string (short social proof tagline)",
  "seo_title": "string (<60 chars)",
  "seo_description": "string (150-160 chars)",
  "og_title": "string",
  "og_description": "string",
  "color_primary": "#hex",
  "color_secondary": "#hex",
  "font_heading": "Google Font Name",
  "font_body": "Google Font Name",
  "hero_image_keyword": "string (unsplash search term for hero bg)"
}

Return ONLY valid JSON. No extra keys, no wrapping, no explanation."""


def _build_content_prompt(business_data: dict) -> str:
    """Build the user prompt from scraped business data.

    Formats all available business data fields into a structured prompt
    that Claude can use to generate website content.

    Args:
        business_data: Dict of scraped business information. Expected keys
            include name, description, address, phone, hours, services,
            reviews, photos, etc. All keys are optional.

    Returns:
        Formatted user prompt string.
    """
    parts: list[str] = ["Generate website content for the following business:\n"]

    # Core identity
    if business_data.get("name"):
        parts.append(f"Business Name: {business_data['name']}")
    if business_data.get("category") or business_data.get("type"):
        parts.append(f"Category: {business_data.get('category') or business_data.get('type')}")
    if business_data.get("description"):
        parts.append(f"Description: {business_data['description']}")

    # Contact and location
    if business_data.get("address"):
        parts.append(f"Address: {business_data['address']}")
    if business_data.get("phone"):
        parts.append(f"Phone: {business_data['phone']}")
    if business_data.get("email"):
        parts.append(f"Email: {business_data['email']}")
    if business_data.get("website"):
        parts.append(f"Website: {business_data['website']}")

    # Hours
    if business_data.get("hours"):
        hours = business_data["hours"]
        if isinstance(hours, dict):
            hours_str = ", ".join(f"{day}: {time}" for day, time in hours.items())
        elif isinstance(hours, list):
            hours_str = ", ".join(str(h) for h in hours)
        else:
            hours_str = str(hours)
        parts.append(f"Business Hours: {hours_str}")

    # Services
    if business_data.get("services"):
        services = business_data["services"]
        if isinstance(services, list):
            services_str = ", ".join(str(s) for s in services)
        else:
            services_str = str(services)
        parts.append(f"Services Offered: {services_str}")

    # Reviews — only include 4-5 star reviews for the generated site
    if business_data.get("reviews"):
        reviews = business_data["reviews"]
        if isinstance(reviews, list):
            good_reviews = [
                r for r in reviews
                if isinstance(r, dict) and (r.get("rating") or 5) >= 4
            ]
            parts.append(f"\nCustomer Reviews ({len(good_reviews)} positive reviews of {len(reviews)} total):")
            for i, review in enumerate(good_reviews[:10], 1):
                author = review.get("author", "Anonymous")
                rating = review.get("rating", "N/A")
                text = review.get("text", "")
                parts.append(f"  {i}. {author} ({rating} stars): {text[:300]}")

    # Rating
    if business_data.get("rating"):
        parts.append(f"Overall Rating: {business_data['rating']}")
    if business_data.get("review_count"):
        parts.append(f"Total Reviews: {business_data['review_count']}")

    # Photos
    if business_data.get("photos"):
        photos = business_data["photos"]
        if isinstance(photos, list):
            parts.append(f"Photos Available: {len(photos)}")

    # Any extra fields we haven't explicitly handled
    handled_keys = {
        "name", "category", "type", "description", "address", "phone",
        "email", "website", "hours", "services", "reviews", "rating",
        "review_count", "photos",
    }
    extra = {k: v for k, v in business_data.items() if k not in handled_keys and v}
    if extra:
        parts.append("\nAdditional Information:")
        for key, value in extra.items():
            # Truncate very long values
            val_str = str(value)
            if len(val_str) > 500:
                val_str = val_str[:500] + "..."
            parts.append(f"  {key}: {val_str}")

    return "\n".join(parts)


def _extract_json_from_response(text: str) -> dict:
    """Extract and parse JSON from Claude's response text.

    Handles cases where the response might include markdown code fences
    or surrounding text despite the system prompt instructions.

    Args:
        text: Raw response text from Claude.

    Returns:
        Parsed JSON as a dictionary.

    Raises:
        ValueError: If no valid JSON can be extracted from the response.
    """
    # First, try parsing the entire text as JSON directly
    stripped = text.strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass

    # Try extracting from markdown code fences
    fence_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", stripped, re.DOTALL)
    if fence_match:
        try:
            return json.loads(fence_match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Try finding the first { ... } block
    brace_match = re.search(r"\{.*\}", stripped, re.DOTALL)
    if brace_match:
        try:
            return json.loads(brace_match.group(0))
        except json.JSONDecodeError:
            pass

    raise ValueError(
        f"Could not extract valid JSON from Claude response. "
        f"Response preview: {stripped[:200]}..."
    )


async def generate_site_content(
    business_data: dict,
    callback: ProgressCallback = None,
) -> SiteContent:
    """Generate website content from scraped business data using Claude API.

    Sends the business data to Claude with a structured prompt that requests
    JSON output matching the SiteContent schema. Parses and validates the
    response into a SiteContent Pydantic model.

    Args:
        business_data: Dictionary of scraped business information containing
            fields like name, description, address, phone, services, reviews, etc.
        callback: Optional async callable that receives progress message strings.
            Used for real-time status updates (e.g., via WebSocket).

    Returns:
        SiteContent with all generated copy and design tokens.

    Raises:
        ValueError: If Claude's response cannot be parsed into valid JSON.
        anthropic.APIError: If the Claude API call fails.
    """
    if callback:
        await callback("Preparing content generation prompt...")

    user_prompt = _build_content_prompt(business_data)

    if callback:
        await callback("Calling Claude API to generate website content...")

    client = _get_anthropic_client()

    response = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        system=CONTENT_GENERATION_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw_text = response.content[0].text

    if callback:
        await callback("Parsing AI-generated content...")

    parsed = _extract_json_from_response(raw_text)
    content = SiteContent(**parsed)

    if callback:
        await callback("Content generation complete.")

    return content


# ═══════════════════════════════════════════════════════════
# HTML RENDERING
# ═══════════════════════════════════════════════════════════


def _escape_html(text: str) -> str:
    """Escape HTML special characters in user/AI-generated text.

    Args:
        text: Raw text string.

    Returns:
        HTML-safe string with &, <, >, and " escaped.
    """
    if not text:
        return ""
    return (
        str(text).replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _render_stars(rating: Any) -> str:
    """Render a star rating as HTML spans.

    Args:
        rating: Numeric rating (1-5). Non-numeric values default to 5.

    Returns:
        HTML string of filled/empty star spans.
    """
    try:
        count = int(float(rating))
    except (ValueError, TypeError):
        count = 5
    count = max(1, min(5, count))
    filled = '<span class="text-yellow-400">&#9733;</span>' * count
    empty = '<span class="text-gray-300">&#9733;</span>' * (5 - count)
    return filled + empty


def render_site_html(
    business_data: dict,
    content: SiteContent,
    template_name: str = "modern",
) -> str:
    """Render a complete, standalone HTML page from business data and AI content.

    Produces a self-contained responsive page using TailwindCSS (CDN) and
    Google Fonts. All styles are inline or via CDN -- no external assets
    needed beyond the CDN links.

    Args:
        business_data: Original scraped business data dict. Used for contact
            info (phone, address, hours) and photo URLs.
        content: AI-generated SiteContent with copy and design tokens.
        template_name: Template variant name (currently only "modern" is
            implemented). Reserved for future template expansion.

    Returns:
        Complete HTML string ready to be saved to a file or served directly.
    """
    # Escape content for safe HTML embedding
    hero_headline = _escape_html(content.hero_headline)
    hero_subheadline = _escape_html(content.hero_subheadline)
    about_title = _escape_html(content.about_title)
    about_text = _escape_html(content.about_text)
    cta_headline = _escape_html(content.cta_headline)
    cta_button_text = _escape_html(content.cta_button_text)
    seo_title = _escape_html(content.seo_title)
    seo_description = _escape_html(content.seo_description)

    business_name = _escape_html(business_data.get("name", "Our Business"))
    phone = _escape_html(business_data.get("phone", ""))
    address = _escape_html(business_data.get("address", ""))
    email = _escape_html(business_data.get("email", ""))

    # Format hours for display
    hours_data = business_data.get("hours")
    hours_html = ""
    if hours_data:
        if isinstance(hours_data, dict):
            hours_lines = [
                f"<li><span class='font-semibold'>{_escape_html(str(day))}:</span> {_escape_html(str(time))}</li>"
                for day, time in hours_data.items()
            ]
            hours_html = "<ul class='space-y-1'>" + "\n".join(hours_lines) + "</ul>"
        elif isinstance(hours_data, list):
            hours_lines = [
                f"<li>{_escape_html(str(h))}</li>" for h in hours_data
            ]
            hours_html = "<ul class='space-y-1'>" + "\n".join(hours_lines) + "</ul>"
        else:
            hours_html = f"<p>{_escape_html(str(hours_data))}</p>"

    # Google Fonts URL
    heading_font = content.font_heading.replace(" ", "+")
    body_font = content.font_body.replace(" ", "+")
    fonts_url = (
        f"https://fonts.googleapis.com/css2?"
        f"family={heading_font}:wght@400;600;700&"
        f"family={body_font}:wght@300;400;500;600&"
        f"display=swap"
    )

    # Build services HTML
    services_cards = ""
    for svc in content.services:
        svc_name = _escape_html(str(svc.get("name", "")))
        svc_desc = _escape_html(str(svc.get("description", "")))
        svc_icon = _escape_html(str(svc.get("icon_suggestion", "star")))
        services_cards += f"""
            <div class="bg-white rounded-xl shadow-md p-6 hover:shadow-lg transition-shadow duration-300">
                <div class="w-12 h-12 rounded-lg flex items-center justify-center mb-4"
                     style="background-color: {content.color_primary}20;">
                    <span class="text-2xl" style="color: {content.color_primary};"
                          title="{svc_icon}">&#9881;</span>
                </div>
                <h3 class="text-xl font-semibold mb-2"
                    style="font-family: '{content.font_heading}', sans-serif;">
                    {svc_name}
                </h3>
                <p class="text-gray-600 leading-relaxed">{svc_desc}</p>
            </div>"""

    # Build testimonials HTML
    testimonials_cards = ""
    for testimonial in content.testimonials:
        t_author = _escape_html(str(testimonial.get("author", "Anonymous")))
        t_text = _escape_html(str(testimonial.get("text", "")))
        t_rating = testimonial.get("rating", 5)
        stars = _render_stars(t_rating)
        testimonials_cards += f"""
            <div class="bg-white rounded-xl shadow-md p-6">
                <div class="mb-3">{stars}</div>
                <p class="text-gray-700 italic mb-4 leading-relaxed">&ldquo;{t_text}&rdquo;</p>
                <p class="font-semibold text-gray-900"
                   style="font-family: '{content.font_heading}', sans-serif;">
                    {t_author}
                </p>
            </div>"""

    # Build photo gallery HTML (if photos are available)
    photos = business_data.get("photos", [])
    photo_gallery_html = ""
    if photos and isinstance(photos, list):
        photo_items = ""
        for i, photo_url in enumerate(photos[:6]):
            url = _escape_html(str(photo_url)) if isinstance(photo_url, str) else ""
            if not url:
                continue
            photo_items += f"""
                <div class="overflow-hidden rounded-lg shadow-md">
                    <img src="{url}" alt="{business_name} photo {i + 1}"
                         class="w-full h-48 object-cover hover:scale-105 transition-transform duration-300"
                         loading="lazy" />
                </div>"""
        if photo_items:
            photo_gallery_html = f"""
        <section class="py-16 px-4" style="background-color: {content.color_primary}08;">
            <div class="max-w-6xl mx-auto">
                <h2 class="text-3xl font-bold text-center mb-10"
                    style="font-family: '{content.font_heading}', sans-serif; color: {content.color_primary};">
                    Gallery
                </h2>
                <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                    {photo_items}
                </div>
            </div>
        </section>"""

    # Build contact details HTML
    contact_items = ""
    if phone:
        contact_items += f"""
                <div class="flex items-start space-x-3">
                    <span class="text-xl mt-1" style="color: {content.color_primary};">&#9742;</span>
                    <div>
                        <p class="font-semibold">Phone</p>
                        <a href="tel:{phone}" class="text-gray-600 hover:underline">{phone}</a>
                    </div>
                </div>"""
    if email:
        contact_items += f"""
                <div class="flex items-start space-x-3">
                    <span class="text-xl mt-1" style="color: {content.color_primary};">&#9993;</span>
                    <div>
                        <p class="font-semibold">Email</p>
                        <a href="mailto:{email}" class="text-gray-600 hover:underline">{email}</a>
                    </div>
                </div>"""
    if address:
        contact_items += f"""
                <div class="flex items-start space-x-3">
                    <span class="text-xl mt-1" style="color: {content.color_primary};">&#9873;</span>
                    <div>
                        <p class="font-semibold">Address</p>
                        <p class="text-gray-600">{address}</p>
                    </div>
                </div>"""

    hours_section = ""
    if hours_html:
        hours_section = f"""
                <div class="flex items-start space-x-3">
                    <span class="text-xl mt-1" style="color: {content.color_primary};">&#9200;</span>
                    <div>
                        <p class="font-semibold mb-1">Hours</p>
                        <div class="text-gray-600 text-sm">{hours_html}</div>
                    </div>
                </div>"""

    # Build external dofollow links for nav and footer
    # These pass SEO link juice to the business's real web properties
    website_url = _escape_html(business_data.get("website", ""))
    website_data = business_data.get("website_data", {})
    social_links = website_data.get("social_links", {}) if website_data else {}
    logo_url = (website_data.get("logo_url", "") or "") if website_data else ""

    # Nav external links (dofollow — no rel="nofollow")
    nav_external_links = ""
    if website_url:
        nav_external_links += (
            f'<a href="{website_url}" class="hover:text-gray-900 transition-colors">Website</a>'
        )
    for platform, url in social_links.items():
        icon = {
            "facebook": "&#xf09a;",
            "instagram": "&#xf16d;",
            "twitter": "&#xf099;",
            "youtube": "&#xf167;",
            "tiktok": "&#xe07b;",
            "linkedin": "&#xf0e1;",
            "yelp": "&#xf1e9;",
        }.get(platform, "")
        label = _escape_html(platform.capitalize())
        safe_url = _escape_html(str(url))
        nav_external_links += f'<a href="{safe_url}" class="hover:text-gray-900 transition-colors">{label}</a>'

    # Footer social links (dofollow with visible icons)
    footer_social_html = ""
    if social_links:
        social_items = ""
        for platform, url in social_links.items():
            label = _escape_html(platform.capitalize())
            safe_url = _escape_html(str(url))
            social_items += (
                f'<a href="{safe_url}" class="hover:text-white transition-colors">{label}</a>'
            )
        footer_social_html = f"""
            <div class="flex justify-center space-x-4 mb-4 text-sm">
                {social_items}
            </div>"""

    # Use logo from website scrape if available
    nav_logo_html = ""
    if logo_url:
        safe_logo = _escape_html(logo_url)
        nav_logo_html = (
            f'<a href="#" class="flex items-center space-x-2">'
            f'<img src="{safe_logo}" alt="{business_name}" class="h-8 w-auto" />'
            f'<span class="text-2xl font-bold" style="font-family: \'{content.font_heading}\', sans-serif; '
            f'color: {content.color_primary};">{business_name}</span></a>'
        )
    else:
        nav_logo_html = (
            f'<a href="#" class="text-2xl font-bold" '
            f'style="font-family: \'{content.font_heading}\', sans-serif; '
            f'color: {content.color_primary};">{business_name}</a>'
        )

    # Assemble the complete HTML page
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{seo_title}</title>
    <meta name="description" content="{seo_description}" />
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="{fonts_url}" rel="stylesheet" />
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {{
            font-family: '{content.font_body}', sans-serif;
        }}
        h1, h2, h3, h4, h5, h6 {{
            font-family: '{content.font_heading}', sans-serif;
        }}
        .btn-primary {{
            background-color: {content.color_primary};
            transition: filter 0.2s ease;
        }}
        .btn-primary:hover {{
            filter: brightness(1.1);
        }}
        .bg-primary {{
            background-color: {content.color_primary};
        }}
        .text-primary {{
            color: {content.color_primary};
        }}
        .bg-secondary {{
            background-color: {content.color_secondary};
        }}
        .text-secondary {{
            color: {content.color_secondary};
        }}
    </style>
</head>
<body class="bg-gray-50 text-gray-800 antialiased">

    <!-- ════════════ NAVIGATION ════════════ -->
    <nav class="bg-white shadow-sm sticky top-0 z-50">
        <div class="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
            {nav_logo_html}
            <div class="hidden md:flex space-x-8 text-sm font-medium text-gray-600">
                <a href="#about" class="hover:text-gray-900 transition-colors">About</a>
                <a href="#services" class="hover:text-gray-900 transition-colors">Services</a>
                <a href="#testimonials" class="hover:text-gray-900 transition-colors">Testimonials</a>
                <a href="#contact" class="hover:text-gray-900 transition-colors">Contact</a>
                {nav_external_links}
            </div>
            <a href="#contact"
               class="btn-primary text-white px-5 py-2 rounded-lg text-sm font-semibold">
                {cta_button_text}
            </a>
        </div>
    </nav>

    <!-- ════════════ HERO SECTION ════════════ -->
    <section class="relative overflow-hidden"
             style="background: linear-gradient(135deg, {content.color_primary}, {content.color_secondary});">
        <div class="max-w-6xl mx-auto px-4 py-24 md:py-32 text-center text-white relative z-10">
            <h1 class="text-4xl md:text-5xl lg:text-6xl font-bold mb-6 leading-tight">
                {hero_headline}
            </h1>
            <p class="text-xl md:text-2xl opacity-90 max-w-2xl mx-auto mb-10 leading-relaxed">
                {hero_subheadline}
            </p>
            <a href="#contact"
               class="inline-block bg-white px-8 py-4 rounded-lg text-lg font-semibold shadow-lg
                      hover:shadow-xl transition-shadow duration-300"
               style="color: {content.color_primary};">
                {cta_button_text}
            </a>
        </div>
        <div class="absolute inset-0 opacity-10">
            <div class="absolute top-10 left-10 w-64 h-64 rounded-full"
                 style="background: {content.color_secondary};"></div>
            <div class="absolute bottom-10 right-10 w-96 h-96 rounded-full"
                 style="background: {content.color_primary};"></div>
        </div>
    </section>

    <!-- ════════════ ABOUT SECTION ════════════ -->
    <section id="about" class="py-20 px-4 bg-white">
        <div class="max-w-4xl mx-auto text-center">
            <h2 class="text-3xl md:text-4xl font-bold mb-6"
                style="color: {content.color_primary};">
                {about_title}
            </h2>
            <p class="text-lg text-gray-600 leading-relaxed max-w-3xl mx-auto">
                {about_text}
            </p>
        </div>
    </section>

    <!-- ════════════ SERVICES SECTION ════════════ -->
    <section id="services" class="py-20 px-4 bg-gray-50">
        <div class="max-w-6xl mx-auto">
            <h2 class="text-3xl md:text-4xl font-bold text-center mb-12"
                style="color: {content.color_primary};">
                Our Services
            </h2>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                {services_cards}
            </div>
        </div>
    </section>

    <!-- ════════════ PHOTO GALLERY (if available) ════════════ -->
    {photo_gallery_html}

    <!-- ════════════ TESTIMONIALS SECTION ════════════ -->
    <section id="testimonials" class="py-20 px-4 bg-gray-50">
        <div class="max-w-6xl mx-auto">
            <h2 class="text-3xl md:text-4xl font-bold text-center mb-12"
                style="color: {content.color_primary};">
                What Our Clients Say
            </h2>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                {testimonials_cards}
            </div>
        </div>
    </section>

    <!-- ════════════ CTA SECTION ════════════ -->
    <section class="py-20 px-4"
             style="background: linear-gradient(135deg, {content.color_primary}, {content.color_secondary});">
        <div class="max-w-3xl mx-auto text-center text-white">
            <h2 class="text-3xl md:text-4xl font-bold mb-6">
                {cta_headline}
            </h2>
            <a href="#contact"
               class="inline-block bg-white px-10 py-4 rounded-lg text-lg font-semibold shadow-lg
                      hover:shadow-xl transition-shadow duration-300"
               style="color: {content.color_primary};">
                {cta_button_text}
            </a>
        </div>
    </section>

    <!-- ════════════ CONTACT SECTION ════════════ -->
    <section id="contact" class="py-20 px-4 bg-white">
        <div class="max-w-4xl mx-auto">
            <h2 class="text-3xl md:text-4xl font-bold text-center mb-12"
                style="color: {content.color_primary};">
                Get In Touch
            </h2>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div class="space-y-6">
                    {contact_items}
                    {hours_section}
                </div>
                <div class="bg-gray-50 rounded-xl p-8">
                    <h3 class="text-xl font-semibold mb-4"
                        style="color: {content.color_primary};">
                        Send Us a Message
                    </h3>
                    <form class="space-y-4" onsubmit="event.preventDefault(); alert('Thank you for your message!');">
                        <input type="text" placeholder="Your Name"
                               class="w-full px-4 py-3 rounded-lg border border-gray-300
                                      focus:outline-none focus:ring-2 focus:border-transparent"
                               style="--tw-ring-color: {content.color_primary};" />
                        <input type="email" placeholder="Your Email"
                               class="w-full px-4 py-3 rounded-lg border border-gray-300
                                      focus:outline-none focus:ring-2 focus:border-transparent"
                               style="--tw-ring-color: {content.color_primary};" />
                        <textarea placeholder="Your Message" rows="4"
                                  class="w-full px-4 py-3 rounded-lg border border-gray-300
                                         focus:outline-none focus:ring-2 focus:border-transparent"
                                  style="--tw-ring-color: {content.color_primary};"></textarea>
                        <button type="submit"
                                class="btn-primary text-white w-full py-3 rounded-lg font-semibold">
                            Send Message
                        </button>
                    </form>
                </div>
            </div>
        </div>
    </section>

    <!-- ════════════ FOOTER ════════════ -->
    <footer class="bg-gray-900 text-gray-400 py-12 px-4">
        <div class="max-w-6xl mx-auto text-center">
            <p class="text-xl font-bold text-white mb-2"
               style="font-family: '{content.font_heading}', sans-serif;">
                {business_name}
            </p>
            <p class="mb-6 text-sm">{address}</p>
            <div class="flex justify-center space-x-6 mb-6 text-sm">
                <a href="#about" class="hover:text-white transition-colors">About</a>
                <a href="#services" class="hover:text-white transition-colors">Services</a>
                <a href="#testimonials" class="hover:text-white transition-colors">Testimonials</a>
                <a href="#contact" class="hover:text-white transition-colors">Contact</a>
            </div>
            {footer_social_html}
            <p class="text-xs text-gray-500">
                &copy; {business_name}. All rights reserved.
            </p>
        </div>
    </footer>

</body>
</html>"""

    return html


# ═══════════════════════════════════════════════════════════
# ORCHESTRATOR
# ═══════════════════════════════════════════════════════════


async def generate_site(
    business_data: dict,
    template_name: str = "modern",
    callback: ProgressCallback = None,
) -> GeneratedSite:
    """Orchestrate end-to-end site generation: content -> HTML -> GeneratedSite.

    This is the main entry point for the site generation pipeline. It:
    1. Generates AI content from business data via Claude API
    2. Renders the content into a complete HTML page
    3. Returns a GeneratedSite with all artifacts

    Args:
        business_data: Dictionary of scraped business information.
        template_name: Template variant to use for rendering (default "modern").
        callback: Optional async callable for progress updates.

    Returns:
        GeneratedSite containing the business name, structured content,
        rendered HTML, and template name.

    Raises:
        ValueError: If content generation or parsing fails.
        anthropic.APIError: If the Claude API call fails.
    """
    if callback:
        await callback("Starting site generation pipeline...")

    # Step 1: Generate content with Claude
    if callback:
        await callback("Step 1/3: Generating website content with AI...")
    content = await generate_site_content(business_data, callback=callback)

    # Step 2: Render HTML
    if callback:
        await callback("Step 2/3: Rendering HTML template...")
    html = render_site_html(business_data, content, template_name=template_name)

    # Step 3: Assemble final output
    if callback:
        await callback("Step 3/3: Assembling final site package...")

    business_name = business_data.get("name", "Generated Site")

    site = GeneratedSite(
        business_name=business_name,
        content=content,
        html=html,
        template_name=template_name,
    )

    if callback:
        await callback(f"Site generation complete for '{business_name}'.")

    return site
