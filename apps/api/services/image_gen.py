"""
Image URL builder — internal SVG generation (zero external dependencies).

Previously used Pollinations.ai (https://image.pollinations.ai), which became
unreliable. Images are now served from the FastAPI backend via the
/api/images/svg endpoint in routers/images.py.

URL format:
  /api/images/svg?type=<type>&title=<title>&content=<content>&seed=<seed>&width=W&height=H

The Next.js frontend proxies /api/* to the FastAPI backend, so these relative
paths resolve correctly in both development and production.
"""
import hashlib
import logging
from urllib.parse import quote

logger = logging.getLogger(__name__)

SVG_ENDPOINT = "/api/images/svg"


def _seed_from_text(text: str) -> str:
    """Derive a stable hex seed string from text."""
    return hashlib.md5(text.encode()).hexdigest()[:12]


def _enc(text: str, max_len: int = 200) -> str:
    """URL-encode a string, truncating to max_len characters first."""
    return quote(text[:max_len], safe="")


def build_image_url(
    slide_type: str,
    title: str = "",
    content: str = "",
    idea: str = "",
    tagline: str = "",
    width: int = 1280,
    height: int = 720,
    seed: str = "",
) -> str:
    """
    Build an internal /api/images/svg URL.

    Parameters
    ----------
    slide_type : One of: hero, og, problem, solution, market, product,
                         business, traction, gtm, competition, team, ask, default
    title      : Slide title text
    content    : Slide body content snippet
    idea       : Original startup idea (used for hero/og)
    tagline    : OG tagline
    width/height : Image dimensions
    seed       : Deterministic seed string
    """
    params = [
        f"type={_enc(slide_type)}",
        f"width={width}",
        f"height={height}",
    ]
    if title:
        params.append(f"title={_enc(title)}")
    if content:
        params.append(f"content={_enc(content)}")
    if idea:
        params.append(f"idea={_enc(idea)}")
    if tagline:
        params.append(f"tagline={_enc(tagline)}")
    if seed:
        params.append(f"seed={_enc(seed)}")

    return f"{SVG_ENDPOINT}?{'&'.join(params)}"


# ── Public helpers (same interface as before) ─────────────────────────────────

def hero_image(idea_text: str) -> str:
    """Landing page hero image for the startup."""
    return build_image_url(
        slide_type="hero",
        idea=idea_text,
        width=1280,
        height=720,
        seed=_seed_from_text(idea_text),
    )


def og_image(idea_text: str, tagline: str = "") -> str:
    """Open Graph social sharing image (1200×630)."""
    return build_image_url(
        slide_type="og",
        idea=idea_text,
        tagline=tagline,
        width=1200,
        height=630,
        seed=_seed_from_text(idea_text),
    )


def pitch_deck_slide_image(slide_title: str, slide_content: str, idea_text: str) -> str:
    """Per-slide pitch deck illustration."""
    title_lower = slide_title.lower()

    if "problem" in title_lower:
        slide_type = "problem"
    elif "solution" in title_lower:
        slide_type = "solution"
    elif "market" in title_lower or "opportunity" in title_lower:
        slide_type = "market"
    elif "product" in title_lower:
        slide_type = "product"
    elif "business model" in title_lower or "revenue" in title_lower:
        slide_type = "business"
    elif "traction" in title_lower:
        slide_type = "traction"
    elif "go-to-market" in title_lower or "gtm" in title_lower:
        slide_type = "gtm"
    elif "competition" in title_lower or "competitive" in title_lower:
        slide_type = "competition"
    elif "team" in title_lower:
        slide_type = "team"
    elif "ask" in title_lower or "funding" in title_lower or "investment" in title_lower:
        slide_type = "ask"
    else:
        slide_type = "default"

    return build_image_url(
        slide_type=slide_type,
        title=slide_title,
        content=slide_content,
        idea=idea_text,
        width=1280,
        height=720,
        seed=_seed_from_text(slide_title + idea_text),
    )


def architecture_diagram(tech_stack: dict, system_design: str, idea_text: str) -> str:
    """System architecture diagram for the MVP tech stack."""
    content = f"{system_design[:100]}"
    if isinstance(tech_stack, dict):
        stack_parts = list(tech_stack.values())[:3]
        content = " → ".join(str(s) for s in stack_parts)
    return build_image_url(
        slide_type="product",
        title="System Architecture",
        content=content,
        idea=idea_text,
        width=1280,
        height=720,
        seed=_seed_from_text(idea_text + "arch"),
    )


def tech_stack_image(tech_stack: dict, idea_text: str) -> str:
    """Technology logos and stack visualization."""
    stack_str = " + ".join(list(tech_stack.values())[:4]) if isinstance(tech_stack, dict) else "Modern Tech Stack"
    return build_image_url(
        slide_type="product",
        title="Tech Stack",
        content=stack_str,
        idea=idea_text,
        width=1280,
        height=500,
        seed=_seed_from_text(idea_text + "stack"),
    )


def market_opportunity_image(tam: str, sam: str, som: str, idea_text: str) -> str:
    """TAM/SAM/SOM market size visualization."""
    return build_image_url(
        slide_type="market",
        title="Market Opportunity",
        content=f"TAM: {tam} | SAM: {sam} | SOM: {som}",
        idea=idea_text,
        width=1280,
        height=720,
        seed=_seed_from_text(idea_text + "market"),
    )


def competitive_landscape_image(competitors: list, idea_text: str) -> str:
    """Competitive landscape visualization."""
    comp_str = ", ".join(competitors[:3]) if competitors else "existing solutions"
    return build_image_url(
        slide_type="competition",
        title="Competitive Landscape",
        content=f"vs {comp_str}",
        idea=idea_text,
        width=1280,
        height=720,
        seed=_seed_from_text(idea_text + "competition"),
    )
