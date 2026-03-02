"""
SVG image generation router — zero external dependencies.

Serves themed SVG slides for the pitch deck and social sharing previews.
Each image type has a distinct color palette, icon, and layout that matches
the slide topic (problem, solution, market, etc.).

Endpoint:
  GET /api/images/svg?type=<type>&title=<title>&content=<content>&seed=<seed>
  → Returns an SVG image (image/svg+xml) with appropriate styling.
"""
import hashlib
import textwrap
from urllib.parse import unquote_plus
from fastapi import APIRouter, Query
from fastapi.responses import Response

router = APIRouter(prefix="/api/images", tags=["images"])


# ── Colour palettes per slide type ────────────────────────────────────────────
PALETTES = {
    "hero":        {"bg1": "#0f0524", "bg2": "#1a0a3d", "accent": "#7c3aed", "accent2": "#4f46e5", "icon": "⚡"},
    "og":          {"bg1": "#0a0a1a", "bg2": "#1e1040", "accent": "#8b5cf6", "accent2": "#6366f1", "icon": "🚀"},
    "problem":     {"bg1": "#1a0a0a", "bg2": "#2d1010", "accent": "#ef4444", "accent2": "#dc2626", "icon": "⚠️"},
    "solution":    {"bg1": "#0a1a0a", "bg2": "#0d2e0d", "accent": "#22c55e", "accent2": "#16a34a", "icon": "✅"},
    "market":      {"bg1": "#0a0f1a", "bg2": "#0d1a30", "accent": "#3b82f6", "accent2": "#2563eb", "icon": "📊"},
    "product":     {"bg1": "#0f0a1a", "bg2": "#1a0f30", "accent": "#a855f7", "accent2": "#9333ea", "icon": "💻"},
    "business":    {"bg1": "#0a1a0a", "bg2": "#0d2010", "accent": "#10b981", "accent2": "#059669", "icon": "💰"},
    "traction":    {"bg1": "#0a1a0f", "bg2": "#0d2a18", "accent": "#34d399", "accent2": "#10b981", "icon": "📈"},
    "gtm":         {"bg1": "#1a100a", "bg2": "#2d1a0a", "accent": "#f59e0b", "accent2": "#d97706", "icon": "🎯"},
    "competition": {"bg1": "#0a0f1a", "bg2": "#101828", "accent": "#06b6d4", "accent2": "#0891b2", "icon": "🏆"},
    "team":        {"bg1": "#1a0a10", "bg2": "#2d0d1a", "accent": "#ec4899", "accent2": "#db2777", "icon": "👥"},
    "ask":         {"bg1": "#0f0f0a", "bg2": "#1a1a0a", "accent": "#eab308", "accent2": "#ca8a04", "icon": "💎"},
    "default":     {"bg1": "#0a0a14", "bg2": "#141428", "accent": "#7c3aed", "accent2": "#4f46e5", "icon": "📋"},
}


def _get_palette(slide_type: str) -> dict:
    """Return palette for slide type, falling back to 'default'."""
    return PALETTES.get(slide_type.lower(), PALETTES["default"])


def _stable_seed(text: str) -> int:
    """Derive a stable int from text for deterministic random-ish values."""
    return int(hashlib.md5(text.encode()).hexdigest()[:8], 16)


def _wrap_text(text: str, max_chars: int = 48) -> list[str]:
    """Wrap text into lines of at most max_chars."""
    return textwrap.wrap(text, max_chars) if text else []


def _escape_svg(text: str) -> str:
    """Escape special XML characters for SVG text content."""
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;"))


def _decorative_circles(seed: int, accent: str, accent2: str) -> str:
    """Generate deterministic decorative blurred circles in the background."""
    circles = []
    positions = [
        (seed % 300 + 900, seed % 200 + 50, 200, 0.12),
        ((seed * 7) % 400 + 600, (seed * 3) % 300 + 300, 160, 0.08),
        ((seed * 13) % 300 + 50, (seed * 5) % 200 + 100, 120, 0.10),
        ((seed * 11) % 200 + 200, (seed * 17) % 250 + 500, 140, 0.07),
    ]
    for i, (cx, cy, r, opacity) in enumerate(positions):
        color = accent if i % 2 == 0 else accent2
        circles.append(
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{color}" '
            f'fill-opacity="{opacity}" filter="url(#blur)"/>'
        )
    return "\n  ".join(circles)


def generate_slide_svg(
    slide_type: str,
    title: str,
    content: str,
    width: int = 1280,
    height: int = 720,
    seed_str: str = "",
) -> str:
    """
    Generate a fully self-contained SVG for a pitch deck slide.

    Parameters
    ----------
    slide_type : Slide category key (problem, solution, market, …)
    title      : Slide title text
    content    : Slide body content (short excerpt shown)
    width/height: Output dimensions
    seed_str   : Seed string for deterministic decoration
    """
    p = _get_palette(slide_type)
    seed = _stable_seed(seed_str or title or slide_type)
    icon = p["icon"]

    # Wrap content to multiple lines for display
    content_lines = _wrap_text(_escape_svg(content[:200]), max_chars=64)
    content_svg = ""
    for idx, line in enumerate(content_lines[:4]):
        y = 460 + idx * 30
        content_svg += f'\n    <text x="640" y="{y}" font-size="18" fill="#94a3b8" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif">{line}</text>'
    if len(content_lines) > 4:
        content_svg += f'\n    <text x="640" y="{460 + 4 * 30}" font-size="16" fill="#64748b" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif">…</text>'

    title_escaped = _escape_svg(title)
    decorative = _decorative_circles(seed, p["accent"], p["accent2"])

    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{p['bg1']}"/>
      <stop offset="100%" stop-color="{p['bg2']}"/>
    </linearGradient>
    <linearGradient id="accent-grad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="{p['accent']}"/>
      <stop offset="100%" stop-color="{p['accent2']}"/>
    </linearGradient>
    <filter id="blur">
      <feGaussianBlur stdDeviation="60"/>
    </filter>
    <filter id="glow">
      <feGaussianBlur stdDeviation="4" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>

  <!-- Background -->
  <rect width="{width}" height="{height}" fill="url(#bg)"/>

  <!-- Decorative blurred circles -->
  {decorative}

  <!-- Grid dots pattern -->
  <pattern id="dots" x="0" y="0" width="40" height="40" patternUnits="userSpaceOnUse">
    <circle cx="2" cy="2" r="1" fill="{p['accent']}" fill-opacity="0.15"/>
  </pattern>
  <rect width="{width}" height="{height}" fill="url(#dots)"/>

  <!-- Bottom accent bar -->
  <rect x="0" y="{height - 4}" width="{width}" height="4" fill="url(#accent-grad)"/>

  <!-- Top left corner accent -->
  <rect x="0" y="0" width="4" height="{height}" fill="url(#accent-grad)" fill-opacity="0.4"/>

  <!-- Icon circle -->
  <circle cx="640" cy="230" r="70" fill="{p['accent']}" fill-opacity="0.12" stroke="{p['accent']}" stroke-width="1.5" stroke-opacity="0.3"/>
  <circle cx="640" cy="230" r="52" fill="{p['accent']}" fill-opacity="0.08"/>
  <text x="640" y="252" font-size="48" text-anchor="middle" dominant-baseline="auto" filter="url(#glow)">{icon}</text>

  <!-- Title -->
  <text x="640" y="360" font-size="52" font-weight="800" fill="white" text-anchor="middle"
        font-family="system-ui, -apple-system, 'Segoe UI', sans-serif"
        letter-spacing="-1">{title_escaped}</text>

  <!-- Accent underline -->
  <rect x="490" y="378" width="300" height="3" rx="2" fill="url(#accent-grad)"/>

  <!-- Content lines -->
  {content_svg}

  <!-- Slide type badge (top-right) -->
  <rect x="{width - 180}" y="20" width="160" height="32" rx="16"
        fill="{p['accent']}" fill-opacity="0.15" stroke="{p['accent']}" stroke-width="1" stroke-opacity="0.3"/>
  <text x="{width - 100}" y="41" font-size="13" fill="{p['accent']}" text-anchor="middle"
        font-family="system-ui, -apple-system, sans-serif" font-weight="600"
        text-transform="uppercase" letter-spacing="1">{_escape_svg(slide_type.upper())}</text>

  <!-- LaunchForge watermark (bottom-left) -->
  <text x="24" y="{height - 14}" font-size="12" fill="#334155"
        font-family="system-ui, -apple-system, sans-serif">⚡ LaunchForge AI</text>
</svg>"""
    return svg


def generate_og_svg(idea: str, tagline: str, width: int = 1200, height: int = 630) -> str:
    """Generate a branded OG social sharing image."""
    p = _get_palette("og")
    seed = _stable_seed(idea)
    decorative = _decorative_circles(seed, p["accent"], p["accent2"])

    idea_lines = _wrap_text(_escape_svg(idea[:120]), max_chars=52)
    idea_svg = ""
    for idx, line in enumerate(idea_lines[:2]):
        y = 330 + idx * 36
        idea_svg += f'\n    <text x="600" y="{y}" font-size="22" fill="#94a3b8" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif">{line}</text>'

    tagline_escaped = _escape_svg(tagline[:80]) if tagline else ""

    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{p['bg1']}"/>
      <stop offset="100%" stop-color="{p['bg2']}"/>
    </linearGradient>
    <linearGradient id="accent-grad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="{p['accent']}"/>
      <stop offset="100%" stop-color="{p['accent2']}"/>
    </linearGradient>
    <filter id="blur"><feGaussianBlur stdDeviation="60"/></filter>
  </defs>

  <!-- Background -->
  <rect width="{width}" height="{height}" fill="url(#bg)"/>
  {decorative}

  <!-- Grid dots -->
  <pattern id="dots" x="0" y="0" width="40" height="40" patternUnits="userSpaceOnUse">
    <circle cx="2" cy="2" r="1" fill="{p['accent']}" fill-opacity="0.12"/>
  </pattern>
  <rect width="{width}" height="{height}" fill="url(#dots)"/>

  <!-- Logo badge -->
  <rect x="60" y="50" width="200" height="44" rx="22"
        fill="{p['accent']}" fill-opacity="0.15" stroke="{p['accent']}" stroke-width="1" stroke-opacity="0.4"/>
  <text x="160" y="78" font-size="18" fill="{p['accent']}" text-anchor="middle"
        font-family="system-ui, sans-serif" font-weight="700">⚡ LaunchForge AI</text>

  <!-- Main tagline -->
  <text x="600" y="220" font-size="44" font-weight="900" fill="white" text-anchor="middle"
        font-family="system-ui, -apple-system, 'Segoe UI', sans-serif" letter-spacing="-1">
    {tagline_escaped if tagline_escaped else "Launch-Ready Startup in 4 Hours"}
  </text>

  <!-- Accent underline -->
  <rect x="200" y="238" width="800" height="3" rx="2" fill="url(#accent-grad)"/>

  <!-- Idea text -->
  {idea_svg}

  <!-- CTA pill -->
  <rect x="450" y="{height - 100}" width="300" height="48" rx="24"
        fill="url(#accent-grad)" fill-opacity="0.9"/>
  <text x="600" y="{height - 70}" font-size="18" fill="white" text-anchor="middle"
        font-family="system-ui, sans-serif" font-weight="700">Try LaunchForge AI →</text>

  <!-- Bottom bar -->
  <rect x="0" y="{height - 4}" width="{width}" height="4" fill="url(#accent-grad)"/>
</svg>"""
    return svg


def generate_hero_svg(idea: str, width: int = 1280, height: int = 720) -> str:
    """Generate a hero section illustration."""
    p = _get_palette("hero")
    seed = _stable_seed(idea)
    decorative = _decorative_circles(seed, p["accent"], p["accent2"])
    idea_lines = _wrap_text(_escape_svg(idea[:100]), max_chars=55)
    idea_svg = ""
    for idx, line in enumerate(idea_lines[:2]):
        y = 370 + idx * 36
        idea_svg += f'\n    <text x="640" y="{y}" font-size="24" fill="#94a3b8" text-anchor="middle" font-family="system-ui, sans-serif">{line}</text>'

    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{p['bg1']}"/>
      <stop offset="100%" stop-color="{p['bg2']}"/>
    </linearGradient>
    <linearGradient id="accent-grad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="{p['accent']}"/>
      <stop offset="100%" stop-color="{p['accent2']}"/>
    </linearGradient>
    <filter id="blur"><feGaussianBlur stdDeviation="60"/></filter>
  </defs>
  <rect width="{width}" height="{height}" fill="url(#bg)"/>
  {decorative}
  <pattern id="dots" x="0" y="0" width="40" height="40" patternUnits="userSpaceOnUse">
    <circle cx="2" cy="2" r="1" fill="{p['accent']}" fill-opacity="0.15"/>
  </pattern>
  <rect width="{width}" height="{height}" fill="url(#dots)"/>

  <!-- Central orb -->
  <circle cx="640" cy="300" r="120" fill="{p['accent']}" fill-opacity="0.06" stroke="{p['accent']}" stroke-width="1" stroke-opacity="0.2"/>
  <circle cx="640" cy="300" r="80"  fill="{p['accent']}" fill-opacity="0.08" stroke="{p['accent']}" stroke-width="1" stroke-opacity="0.3"/>
  <text x="640" y="320" font-size="64" text-anchor="middle">{p['icon']}</text>

  <!-- Headline -->
  <text x="640" y="478" font-size="42" font-weight="900" fill="white" text-anchor="middle"
        font-family="system-ui, -apple-system, sans-serif" letter-spacing="-1">Idea → Launch-Ready Startup</text>
  <rect x="320" y="492" width="640" height="3" rx="2" fill="url(#accent-grad)"/>
  {idea_svg}
  <rect x="0" y="{height - 4}" width="{width}" height="4" fill="url(#accent-grad)"/>
  <text x="24" y="{height - 14}" font-size="12" fill="#334155" font-family="system-ui, sans-serif">⚡ LaunchForge AI</text>
</svg>"""
    return svg


@router.get("/svg")
async def get_svg_image(
    type: str = Query(default="default", description="Slide type key"),
    title: str = Query(default="", description="Slide title"),
    content: str = Query(default="", description="Slide body content"),
    idea: str = Query(default="", description="Startup idea text (for hero/og)"),
    tagline: str = Query(default="", description="Tagline for OG image"),
    seed: str = Query(default="", description="Seed string for deterministic decorations"),
    width: int = Query(default=1280, ge=100, le=4096),
    height: int = Query(default=720, ge=100, le=4096),
):
    """
    Return a themed SVG image for the given slide type.

    Special types:
    - **og**   → OG social sharing card (1200×630 recommended)
    - **hero** → Landing page hero illustration (1280×720)
    - All others → Pitch deck slide image
    """
    t = type.lower()

    if t == "og":
        svg = generate_og_svg(
            idea=unquote_plus(idea),
            tagline=unquote_plus(tagline),
            width=width,
            height=height,
        )
    elif t == "hero":
        svg = generate_hero_svg(
            idea=unquote_plus(idea),
            width=width,
            height=height,
        )
    else:
        svg = generate_slide_svg(
            slide_type=t,
            title=unquote_plus(title),
            content=unquote_plus(content),
            width=width,
            height=height,
            seed_str=unquote_plus(seed) or unquote_plus(title),
        )

    return Response(
        content=svg,
        media_type="image/svg+xml",
        headers={
            "Cache-Control": "public, max-age=86400, immutable",
            "Vary": "Accept-Encoding",
        },
    )
