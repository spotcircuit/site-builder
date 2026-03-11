"""
Gemini Image Generator Module

Generates AI images for website sections using Google's Gemini API.
Uses gemini-2.5-flash-image for fast, high-quality image generation.

Images are saved to the build directory and referenced in data.json
so React components can use them directly.
"""

import base64
import logging
import os
from pathlib import Path
from typing import Any, Callable, Coroutine, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

ProgressCallback = Optional[Callable[[str], Coroutine[Any, Any, None]]]


class GeneratedImage(BaseModel):
    """Result of a single image generation."""

    section: str = Field(..., description="Which section this image is for (hero, about, etc.)")
    filename: str = Field(..., description="Filename saved to public/ directory")
    prompt: str = Field(..., description="The prompt used to generate the image")


class ImageGenerationResult(BaseModel):
    """Result of all image generation for a site."""

    images: list[GeneratedImage] = Field(default_factory=list)
    hero_image: Optional[str] = Field(default=None, description="Filename of hero background image")
    about_image: Optional[str] = Field(default=None, description="Filename of about section image")
    gallery_images: list[str] = Field(default_factory=list, description="Filenames of gallery images")
    services_image: Optional[str] = Field(default=None, description="Filename of services section image")
    why_choose_us_image: Optional[str] = Field(default=None, description="Filename of why choose us section image")
    contact_image: Optional[str] = Field(default=None, description="Filename of contact section image")
    image_dir: Optional[str] = Field(default=None, description="Directory where images are saved")


def is_gemini_configured() -> bool:
    """Check if Gemini API key is available."""
    return bool(os.environ.get("GEMINI_API_KEY"))


def _build_hero_prompt(business_name: str, category: str, keyword: str) -> str:
    """Build a photorealistic prompt for the hero background image."""
    return (
        f"A stunning, professional wide-angle photograph for a {category} business called "
        f"'{business_name}'. The scene shows a beautiful, inviting {keyword} environment "
        f"with warm, natural lighting. The composition is cinematic with soft depth of field, "
        f"shot on a Canon EOS R5 with a 24mm lens. The mood is welcoming and premium. "
        f"No text, no logos, no watermarks. Photorealistic quality, 4K detail."
    )


def _build_about_prompt(business_name: str, category: str) -> str:
    """Build a prompt for the about section image."""
    return (
        f"A warm, candid photograph showing the interior or workspace of a {category} "
        f"business. The scene conveys professionalism and care, with natural lighting "
        f"streaming in. Shallow depth of field, warm color tones, editorial photography "
        f"style. No text, no logos, no people's faces. Photorealistic."
    )


def _build_gallery_prompt(business_name: str, category: str, index: int) -> str:
    """Build a prompt for a gallery image."""
    angles = [
        "a beautifully composed detail shot",
        "an atmospheric wide-angle interior view",
        "a close-up showcasing quality and craftsmanship",
    ]
    angle = angles[index % len(angles)]
    return (
        f"{angle} of a {category} business environment. Professional photography, "
        f"natural lighting, warm tones, high detail. No text, no logos. Photorealistic."
    )


def _build_services_prompt(business_name: str, category: str) -> str:
    """Build a prompt for the services section image."""
    return (
        f"A professional photograph showcasing the services of a {category} business. "
        f"The image shows tools, equipment, or the work environment that represents "
        f"quality service delivery. Clean composition, professional lighting, warm tones. "
        f"No text, no logos, no faces. Photorealistic editorial style."
    )


def _build_why_choose_us_prompt(business_name: str, category: str) -> str:
    """Build a prompt for the why choose us section image."""
    return (
        f"A confident, trustworthy photograph representing excellence in {category}. "
        f"Shows attention to detail, quality craftsmanship, or a premium environment "
        f"that conveys reliability and expertise. Warm natural lighting, shallow depth "
        f"of field. No text, no logos, no faces. Photorealistic."
    )


def _build_contact_prompt(business_name: str, category: str) -> str:
    """Build a prompt for the contact section image."""
    return (
        f"A welcoming, inviting exterior or entrance photograph of a {category} business "
        f"location. The scene is warm and approachable with good curb appeal, natural "
        f"daylight, and a friendly atmosphere. No text, no logos, no faces. Photorealistic."
    )


async def generate_site_images(
    business_name: str,
    category: str,
    hero_keyword: str,
    has_photos: bool,
    output_dir: Optional[Path] = None,
    callback: ProgressCallback = None,
) -> ImageGenerationResult:
    """Generate AI images for website sections using Gemini.

    Only generates images for sections that don't have real photos from
    Google Maps scraping. Images are saved to output_dir (or a temp dir).

    Args:
        business_name: Name of the business
        category: Business category (e.g. "Pizza Restaurant")
        hero_keyword: Keyword for hero image (from AI content generation)
        has_photos: Whether Google Maps photos are available
        output_dir: Directory to save images (creates temp dir if None)
        callback: Optional progress callback

    Returns:
        ImageGenerationResult with paths to generated images
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.warning("GEMINI_API_KEY not set, skipping image generation")
        return ImageGenerationResult()

    try:
        from google import genai
        from google.genai import types
    except ImportError:
        logger.warning("google-genai package not installed, skipping image generation")
        return ImageGenerationResult()

    client = genai.Client(api_key=api_key)
    result = ImageGenerationResult()

    # Use provided dir or create temp dir for images
    if output_dir is None:
        import tempfile
        output_dir = Path(tempfile.mkdtemp(prefix="site_images_"))
    result.image_dir = str(output_dir)

    public_dir = output_dir
    public_dir.mkdir(parents=True, exist_ok=True)

    async def _generate_and_save(
        prompt: str,
        filename: str,
        section: str,
        aspect_ratio: str = "16:9",
    ) -> Optional[str]:
        """Generate a single image and save it."""
        try:
            if callback:
                await callback(f"Generating {section} image...")

            response = client.models.generate_content(
                model="gemini-2.5-flash-image",
                contents=[prompt],
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                    image_config=types.ImageConfig(
                        aspect_ratio=aspect_ratio,
                        image_size="1K",
                    ),
                ),
            )

            # Extract image from response
            for part in response.parts:
                if part.inline_data is not None:
                    image_data = part.inline_data.data
                    if isinstance(image_data, str):
                        image_data = base64.b64decode(image_data)

                    filepath = public_dir / filename
                    filepath.write_bytes(image_data)

                    result.images.append(
                        GeneratedImage(
                            section=section,
                            filename=filename,
                            prompt=prompt,
                        )
                    )

                    logger.info(f"Generated {section} image: {filename} ({len(image_data)} bytes)")
                    return filename

            logger.warning(f"No image in Gemini response for {section}")
            return None

        except Exception as e:
            logger.error(f"Image generation failed for {section}: {e}")
            if callback:
                await callback(f"Image generation failed for {section} (non-fatal)")
            return None

    # Generate hero image (only if no Google Maps photos)
    if not has_photos:
        if callback:
            await callback("Generating AI hero image...")

        hero_prompt = _build_hero_prompt(business_name, category, hero_keyword or category)
        hero_path = await _generate_and_save(
            prompt=hero_prompt,
            filename="hero-bg.png",
            section="hero",
            aspect_ratio="16:9",
        )
        if hero_path:
            result.hero_image = hero_path

    # ── Section images (always generated — these sections have no real photos) ──

    # About section image (only if no Google Maps photos to use)
    if not has_photos:
        if callback:
            await callback("Generating about section image...")
        about_prompt = _build_about_prompt(business_name, category)
        about_path = await _generate_and_save(
            prompt=about_prompt,
            filename="about.png",
            section="about",
            aspect_ratio="4:3",
        )
        if about_path:
            result.about_image = about_path

    # Services section image
    if callback:
        await callback("Generating services image...")
    services_prompt = _build_services_prompt(business_name, category)
    services_path = await _generate_and_save(
        prompt=services_prompt,
        filename="services.png",
        section="services",
        aspect_ratio="4:3",
    )
    if services_path:
        result.services_image = services_path

    # Why Choose Us section image
    if callback:
        await callback("Generating why-choose-us image...")
    why_prompt = _build_why_choose_us_prompt(business_name, category)
    why_path = await _generate_and_save(
        prompt=why_prompt,
        filename="why-choose-us.png",
        section="why-choose-us",
        aspect_ratio="4:3",
    )
    if why_path:
        result.why_choose_us_image = why_path

    # Contact section image
    if callback:
        await callback("Generating contact image...")
    contact_prompt = _build_contact_prompt(business_name, category)
    contact_path = await _generate_and_save(
        prompt=contact_prompt,
        filename="contact.png",
        section="contact",
        aspect_ratio="16:9",
    )
    if contact_path:
        result.contact_image = contact_path

    # Generate gallery images (only if no Google Maps photos)
    if not has_photos:
        for i in range(3):
            gallery_prompt = _build_gallery_prompt(business_name, category, i)
            gallery_path = await _generate_and_save(
                prompt=gallery_prompt,
                filename=f"gallery-{i + 1}.png",
                section=f"gallery-{i + 1}",
                aspect_ratio="4:3",
            )
            if gallery_path:
                result.gallery_images.append(gallery_path)

    if callback:
        total = len(result.images)
        await callback(f"Generated {total} AI image{'s' if total != 1 else ''}.")

    return result
