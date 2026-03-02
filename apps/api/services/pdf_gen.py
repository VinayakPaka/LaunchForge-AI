"""
PDF generation service for LaunchForge AI launch packages.

Generates one professionally styled PDF per report section:
  01_business_validation.pdf   — Market validation & opportunity score
  02_gtm_strategy.pdf          — Go-to-market plan & monetisation
  03_technical_architecture.pdf — Tech stack & system design
  04_security_audit.pdf        — OWASP Top 10 audit
  05_marketing_kit.pdf         — Landing copy, pitch deck (10 slides)
  06_seo_strategy.pdf          — Keywords, meta tags, content plan
  07_mvp_code.pdf              — Generated source files

All PDFs use a consistent dark-accent brand style:
  - Deep navy background header with ⚡ LaunchForge AI wordmark
  - Purple accent colour (#7C3AED) for headings and rules
  - Clean white body with structured tables and bullet lists
  - Auto page-numbering footer with generation timestamp
"""
from __future__ import annotations

import textwrap
from datetime import datetime, timezone
from io import BytesIO
from typing import Any

from fpdf import FPDF

# ── Brand constants ────────────────────────────────────────────────────────────
BRAND_NAME   = "LaunchForge AI"
SITE_URL     = "https://tb314nms.run.complete.dev"
DATE_STR     = datetime.now(timezone.utc).strftime("%B %d, %Y")

# DejaVu font paths (Unicode-capable, available on this system)
FONT_DIR     = "/usr/share/fonts/truetype/dejavu"
FONT_REGULAR = f"{FONT_DIR}/DejaVuSans.ttf"
FONT_BOLD    = f"{FONT_DIR}/DejaVuSans-Bold.ttf"
FONT_MONO    = f"{FONT_DIR}/DejaVuSansMono.ttf"
FONT_MONO_B  = f"{FONT_DIR}/DejaVuSansMono-Bold.ttf"

# RGB colour palette
C_NAVY       = (10,  10,  30)    # header background
C_PURPLE     = (124, 58,  237)   # accent / section headings
C_PURPLE_LT  = (167, 119, 248)   # lighter purple for sub-headings
C_WHITE      = (255, 255, 255)
C_DARK       = (30,  30,  50)    # body text
C_GRAY       = (100, 100, 130)   # muted text
C_RULE       = (200, 190, 240)   # thin horizontal rule
C_ROW_EVEN   = (245, 243, 255)   # table alternating row
C_ROW_ODD    = (255, 255, 255)
C_TAG_BG     = (237, 233, 254)   # pill/tag background
C_GREEN      = (22,  163,  74)
C_RED        = (220,  38,  38)
C_AMBER      = (217, 119,   6)

MARGIN       = 14   # mm left/right
LINE_H       = 6    # mm standard line height

# ── Per-slide-type colour themes (bg1, bg2, accent RGB) ───────────────────────
SLIDE_THEMES: dict[str, dict] = {
    "problem":     {"bg": (26, 10, 10),  "bg2": (45, 16, 16),  "acc": (239, 68,  68),  "acc2": (220, 38,  38),  "icon": "!"},
    "solution":    {"bg": (10, 26, 10),  "bg2": (13, 46, 13),  "acc": (34,  197, 94),  "acc2": (22,  163, 74),  "icon": "+"},
    "market":      {"bg": (10, 15, 26),  "bg2": (13, 26, 48),  "acc": (59,  130, 246), "acc2": (37,  99,  235), "icon": "~"},
    "product":     {"bg": (15, 10, 26),  "bg2": (26, 15, 48),  "acc": (168, 85,  247), "acc2": (147, 51,  234), "icon": "*"},
    "business":    {"bg": (10, 26, 20),  "bg2": (13, 32, 16),  "acc": (16,  185, 129), "acc2": (5,   150, 105), "icon": "$"},
    "traction":    {"bg": (10, 26, 15),  "bg2": (13, 42, 24),  "acc": (52,  211, 153), "acc2": (16,  185, 129), "icon": "^"},
    "gtm":         {"bg": (26, 16, 10),  "bg2": (45, 26, 10),  "acc": (245, 158, 11),  "acc2": (217, 119, 6),   "icon": ">"},
    "competition": {"bg": (10, 15, 26),  "bg2": (16, 24, 40),  "acc": (6,   182, 212), "acc2": (8,   145, 178), "icon": "#"},
    "team":        {"bg": (26, 10, 16),  "bg2": (45, 13, 26),  "acc": (236, 72,  153), "acc2": (219, 39,  119), "icon": "@"},
    "ask":         {"bg": (15, 15, 10),  "bg2": (26, 26, 10),  "acc": (234, 179, 8),   "acc2": (202, 138, 4),   "icon": "D"},
    "default":     {"bg": (10, 10, 20),  "bg2": (20, 20, 40),  "acc": (124, 58,  237), "acc2": (79,  70,  229), "icon": "-"},
}

def _slide_theme(title: str) -> dict:
    t = title.lower()
    if "problem" in t:           return SLIDE_THEMES["problem"]
    if "solution" in t:          return SLIDE_THEMES["solution"]
    if "market" in t or "opportunit" in t: return SLIDE_THEMES["market"]
    if "product" in t:           return SLIDE_THEMES["product"]
    if "business" in t or "model" in t or "revenue" in t: return SLIDE_THEMES["business"]
    if "traction" in t:          return SLIDE_THEMES["traction"]
    if "go-to" in t or "gtm" in t or "launch" in t: return SLIDE_THEMES["gtm"]
    if "competi" in t:           return SLIDE_THEMES["competition"]
    if "team" in t:              return SLIDE_THEMES["team"]
    if "ask" in t or "fund" in t or "invest" in t: return SLIDE_THEMES["ask"]
    return SLIDE_THEMES["default"]


# ── Base PDF class ─────────────────────────────────────────────────────────────
class _BasePDF(FPDF):
    """FPDF subclass with LaunchForge branding baked in."""

    def __init__(self, section_title: str, idea: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._section_title = section_title
        self._idea = idea[:80]
        self._slide_mode = False   # suppresses header/footer on slide pages
        # Register DejaVu Unicode fonts (no italic variant — map I → regular)
        self.add_font("Sans",  "",  FONT_REGULAR, uni=True)
        self.add_font("Sans",  "B", FONT_BOLD,    uni=True)
        self.add_font("Sans",  "I", FONT_REGULAR, uni=True)   # italic → regular
        self.add_font("Sans",  "BI",FONT_BOLD,    uni=True)   # bold-italic → bold
        self.add_font("Mono",  "",  FONT_MONO,    uni=True)
        self.add_font("Mono",  "B", FONT_MONO_B,  uni=True)
        self.set_margins(MARGIN, 10, MARGIN)
        self.set_auto_page_break(auto=True, margin=18)
        self.add_page()

    # ── Header / Footer (suppressed on slide pages) ─────────────────────────
    def header(self):
        if self._slide_mode:
            return          # slide pages manage their own layout
        # Navy banner
        self.set_fill_color(*C_NAVY)
        self.rect(0, 0, 210, 20, style="F")
        # ⚡ wordmark (left)
        self.set_text_color(*C_WHITE)
        self.set_font("Sans", "B", 11)
        self.set_xy(MARGIN, 5)
        self.cell(60, 10, f">> {BRAND_NAME}", ln=0)
        # Section title (right)
        self.set_font("Sans", "", 9)
        self.set_text_color(*C_PURPLE_LT)
        self.set_xy(70, 5)
        self.cell(210 - 70 - MARGIN, 10, self._section_title,
                  align="R", ln=0)
        self.ln(14)
        self.set_x(MARGIN)   # reset X after header cells
        # Thin purple rule under header
        self.set_draw_color(*C_PURPLE)
        self.set_line_width(0.5)
        self.line(MARGIN, 21, 210 - MARGIN, 21)
        self.ln(4)
        self.set_x(MARGIN)   # ensure cursor is at left margin

    # ── Footer ──────────────────────────────────────────────────────────────
    def footer(self):
        if self._slide_mode:
            return
        self.set_y(-14)
        self.set_draw_color(*C_RULE)
        self.set_line_width(0.3)
        self.line(MARGIN, self.get_y(), 210 - MARGIN, self.get_y())
        self.ln(1)
        self.set_font("Sans", "", 7)
        self.set_text_color(*C_GRAY)
        self.cell(0, 5, f"{BRAND_NAME}  ·  {SITE_URL}  ·  Generated {DATE_STR}",
                  align="L", ln=0)
        self.set_x(-MARGIN - 20)
        self.cell(20, 5, f"Page {self.page_no()}", align="R")

    # ── Layout helpers ──────────────────────────────────────────────────────
    def page_title(self, title: str, subtitle: str = ""):
        """Large section title at top of first page."""
        self.set_font("Sans", "B", 20)
        self.set_text_color(*C_PURPLE)
        self.mcell(0, 10, title, align="L")
        if subtitle:
            self.set_font("Sans", "", 10)
            self.set_text_color(*C_GRAY)
            self.mcell(0, 6, subtitle, align="L")
        # Thick accent rule
        self.set_fill_color(*C_PURPLE)
        self.rect(MARGIN, self.get_y() + 1, 40, 2, style="F")
        self.ln(8)

    def section_heading(self, text: str):
        """Purple H2-level heading with thin rule above."""
        self.ln(3)
        self.set_draw_color(*C_RULE)
        self.set_line_width(0.2)
        self.line(MARGIN, self.get_y(), 210 - MARGIN, self.get_y())
        self.ln(3)
        self.set_font("Sans", "B", 12)
        self.set_text_color(*C_PURPLE)
        self.cell(0, 7, text, ln=1)

    def sub_heading(self, text: str):
        """Lighter purple H3-level sub-heading."""
        self.set_font("Sans", "B", 10)
        self.set_text_color(*C_PURPLE_LT)
        self.cell(0, 6, text, ln=1)
        self.ln(1)

    def mcell(self, w: float, h: float, txt: str, **kwargs):
        """
        multi_cell wrapper that resets X to the left margin after the call.
        fpdf2 >= 2.5.2 leaves the cursor at the right edge after multi_cell;
        this wrapper always returns it to MARGIN so subsequent cells don't
        run off the page.
        """
        self.multi_cell(w, h, txt, **kwargs)
        self.set_x(MARGIN)

    def body_text(self, text: str, color=C_DARK):
        """Wrapped body paragraph."""
        self.set_font("Sans", "", 9)
        self.set_text_color(*color)
        self.mcell(0, LINE_H, _safe(text), align="L")
        self.ln(2)

    def kv_row(self, key: str, value: str, fill: bool = False):
        """Single key → value row (table-like)."""
        fill_color = C_ROW_EVEN if fill else C_ROW_ODD
        self.set_fill_color(*fill_color)
        self.set_font("Sans", "B", 8)
        self.set_text_color(*C_DARK)
        w_key = 50
        self.cell(w_key, LINE_H + 1, _safe(key), border=0, fill=True)
        self.set_font("Sans", "", 8)
        self.set_text_color(*C_GRAY)
        self.mcell(0, LINE_H + 1, _safe(value), border=0, fill=True)
        self.set_fill_color(*C_WHITE)

    def table_header(self, cols: list[tuple[str, float]]):
        """Render a table header row. cols = [(label, width_mm), ...]"""
        self.set_fill_color(*C_NAVY)
        self.set_text_color(*C_WHITE)
        self.set_font("Sans", "B", 8)
        for label, w in cols:
            self.cell(w, LINE_H + 2, label, border=0, fill=True, align="C")
        self.ln()

    def table_row(self, cells: list[tuple[str, float]], even: bool = False):
        """Render a single data row."""
        self.set_fill_color(*(C_ROW_EVEN if even else C_ROW_ODD))
        self.set_text_color(*C_DARK)
        self.set_font("Sans", "", 8)
        x0 = self.get_x()
        y0 = self.get_y()
        max_h = LINE_H + 1
        for text, w in cells:
            self.mcell(w, LINE_H + 1, _safe(text)[:120], border=0,
                            fill=True, align="L")
            self.set_xy(x0 + w, y0)
            x0 += w
        self.set_y(y0 + max_h)

    def bullet(self, text: str, indent: int = 4, symbol: str = "•"):
        """Single bullet point."""
        self.set_font("Sans", "", 9)
        self.set_text_color(*C_DARK)
        effective_w = 210 - 2 * MARGIN - indent
        lines = textwrap.wrap(_safe(text), int(effective_w * 2.2))
        first = True
        for line in lines:
            self.set_x(MARGIN + indent)
            prefix = f"{symbol}  " if first else "   "
            self.cell(effective_w, LINE_H, prefix + line, ln=1)
            first = False
        if not lines:
            self.set_x(MARGIN + indent)
            self.cell(effective_w, LINE_H, f"{symbol}  {_safe(text)}", ln=1)

    def tag_pills(self, items: list[str], max_per_row: int = 5):
        """Render keyword/tag pills in rows."""
        if not items:
            return
        self.set_font("Sans", "", 8)
        x_start = MARGIN
        x = x_start
        y = self.get_y()
        pill_h = 6
        for item in items[:40]:
            label = _safe(str(item))[:30]
            w = self.get_string_width(label) + 6
            if x + w > 210 - MARGIN:
                x = x_start
                y += pill_h + 2
                self.set_y(y)
            self.set_fill_color(*C_TAG_BG)
            self.set_draw_color(*C_PURPLE_LT)
            self.set_line_width(0.2)
            self.rect(x, y, w, pill_h, style="FD")
            self.set_text_color(*C_PURPLE)
            self.set_xy(x + 2, y + 0.8)
            self.cell(w - 4, pill_h - 1.5, label, ln=0)
            x += w + 3
        self.set_y(y + pill_h + 4)

    def severity_badge(self, status: str) -> tuple[int, int, int]:
        """Return colour for PASS/WARN/FAIL/Critical/High/Medium/Low."""
        s = status.upper()
        if s in ("PASS", "LOW", "CLEAR"):    return C_GREEN
        if s in ("WARN", "MEDIUM", "INFO"):  return C_AMBER
        return C_RED

    def code_block(self, code: str, max_lines: int = 30):
        """Monospace code block with dark background."""
        lines = code.splitlines()[:max_lines]
        self.set_fill_color(20, 20, 40)
        self.set_text_color(160, 200, 100)
        self.set_font("Mono", "", 7)
        block_h = len(lines) * 4.5 + 4
        self.rect(MARGIN, self.get_y(), 210 - 2 * MARGIN, block_h, style="F")
        self.ln(2)
        for line in lines:
            self.set_x(MARGIN + 3)
            self.cell(0, 4.5, line[:110], ln=1)
        self.ln(3)
        self.set_text_color(*C_DARK)

    def info_box(self, text: str, color=C_PURPLE):
        """Coloured info/callout box."""
        self.set_fill_color(*C_TAG_BG)
        self.set_draw_color(*color)
        self.set_line_width(0.8)
        h = max(10, len(textwrap.wrap(_safe(text), 90)) * 6 + 4)
        self.rect(MARGIN, self.get_y(), 210 - 2 * MARGIN, h, style="FD")
        self.set_xy(MARGIN + 3, self.get_y() + 2)
        self.set_font("Sans", "I", 9)
        self.set_text_color(*C_DARK)
        self.mcell(210 - 2 * MARGIN - 6, 6, _safe(text))
        self.ln(3)


    # ── Beautiful full-page pitch deck slide ────────────────────────────────
    def draw_slide_page(
        self,
        slide_num: int,
        total: int,
        title: str,
        content: str,
        speaker_note: str = "",
    ):
        """
        Render one pitch deck slide as a full A4 page.

        Layout (portrait, 210 × 297 mm):
        ┌─────────────────────────────────────┐  y=0
        │  [full dark bg]                     │
        │                                     │
        │  [large icon text  - centered]      │  y≈55
        │                                     │
        │  [TITLE — 30pt bold white centered] │  y≈95
        │  [thin accent underline bar]        │  y≈111
        │                                     │
        │  ┌─ content card ─────────────────┐ │  y≈125
        │  │ content text (12pt)            │ │
        │  └────────────────────────────────┘ │  y≈220
        │                                     │
        │  ┌─ speaker notes ────────────────┐ │  y≈232
        │  │ italic 8pt notes text          │ │
        │  └────────────────────────────────┘ │  y≈270
        │                                     │
        │  [LaunchForge AI · slide N/total]   │  y≈285
        └─────────────────────────────────────┘  y=297
        """
        theme = _slide_theme(title)
        bg     = theme["bg"]
        bg2    = theme["bg2"]
        acc    = theme["acc"]
        acc2   = theme["acc2"]
        icon   = theme["icon"]

        W, H = 210, 297   # A4 portrait mm

        # ── Enter slide mode & add blank page ──────────────────────────────
        self._slide_mode = True
        self.set_auto_page_break(False)
        self.add_page()

        # ── Full background (two-tone vertical split) ───────────────────────
        self.set_fill_color(*bg)
        self.rect(0, 0, W, H, style="F")
        # Lighter bottom-half overlay for depth
        self.set_fill_color(*bg2)
        self.rect(0, H * 0.5, W, H * 0.5, style="F")

        # ── Subtle diagonal accent bars (decorative) ────────────────────────
        self.set_fill_color(*acc)
        # Top-left corner accent block
        self.set_alpha = lambda a: None   # fpdf2 doesn't support true alpha; simulate with color
        self.rect(0, 0, 4, H, style="F")
        # Top-right thin bar
        self.rect(W - 2, 0, 2, H * 0.6, style="F")

        # ── Slide number badge (top-right circle area) ──────────────────────
        badge_x, badge_y, badge_r = W - 28, 18, 12
        # Badge circle (filled square as approximation)
        self.set_fill_color(*acc)
        self.rect(badge_x - badge_r, badge_y - badge_r, badge_r * 2, badge_r * 2, style="F")
        self.set_text_color(*C_WHITE)
        self.set_font("Sans", "B", 14)
        self.set_xy(badge_x - badge_r, badge_y - 5)
        self.cell(badge_r * 2, 10, str(slide_num), align="C", ln=0)

        # Total slides counter (smaller, under badge)
        self.set_font("Sans", "", 7)
        self.set_text_color(*acc2)
        self.set_xy(badge_x - badge_r, badge_y + 6)
        self.cell(badge_r * 2, 5, f"of {total}", align="C", ln=0)

        # ── Category label (top-left under accent bar) ───────────────────────
        self.set_font("Sans", "B", 7)
        self.set_text_color(*acc)
        self.set_xy(10, 12)
        self.cell(60, 5, "INVESTOR PITCH DECK", ln=0)
        self.set_xy(10, 18)
        self.set_font("Sans", "", 7)
        self.set_text_color(80, 80, 120)
        self.cell(60, 5, "LaunchForge AI", ln=0)

        # ── Icon badge (centered, large ASCII symbol in a circle) ────────────
        icon_y = 42
        icon_r = 18
        icon_cx = W / 2
        # Outer glow circle (lighter fill)
        self.set_fill_color(acc[0], acc[1], acc[2])
        # Draw as filled square centered
        self.rect(icon_cx - icon_r, icon_y - icon_r, icon_r * 2, icon_r * 2, style="F")
        # Icon text
        self.set_font("Sans", "B", 24)
        self.set_text_color(*C_WHITE)
        self.set_xy(icon_cx - icon_r, icon_y - 9)
        self.cell(icon_r * 2, 18, icon, align="C", ln=0)

        # ── Title (large, bold, white, centered) ─────────────────────────────
        title_y = 76
        self.set_font("Sans", "B", 28)
        self.set_text_color(*C_WHITE)
        # Wrap long titles
        title_str = _safe(title).upper()
        self.set_xy(16, title_y)
        self.mcell(W - 32, 12, title_str, align="C")

        # ── Accent underline bar under title ──────────────────────────────────
        bar_w = min(80 + len(title_str) * 2, W - 40)
        bar_x = (W - bar_w) / 2
        bar_y = self.get_y() + 2
        # Main accent bar
        self.set_fill_color(*acc)
        self.rect(bar_x, bar_y, bar_w, 2.5, style="F")
        # Thinner secondary bar
        self.set_fill_color(*acc2)
        self.rect(bar_x + bar_w * 0.3, bar_y + 4, bar_w * 0.4, 1, style="F")

        # ── Content card (light translucent bg) ───────────────────────────────
        card_x   = 14
        card_y   = bar_y + 14
        card_w   = W - 28
        card_h   = 120

        # Card background
        self.set_fill_color(255, 255, 255)
        self.rect(card_x, card_y, card_w, card_h, style="F")
        # Left accent strip on card
        self.set_fill_color(*acc)
        self.rect(card_x, card_y, 3, card_h, style="F")

        # Content text inside card
        self.set_xy(card_x + 8, card_y + 8)
        self.set_font("Sans", "", 10)
        self.set_text_color(30, 30, 50)
        # Split content into bullet-like lines
        content_clean = _safe(content)
        # Auto-detect if content has bullet separators
        if ". " in content_clean and len(content_clean) > 60:
            import re
            # Split on sentence boundaries for natural bullet flow
            sentences = re.split(r'(?<=[.!?])\s+', content_clean)
            for sent in sentences[:6]:
                sent = sent.strip()
                if not sent:
                    continue
                self.set_x(card_x + 8)
                self.set_font("Sans", "B", 8)
                self.set_text_color(*acc)
                self.cell(5, 6, "-", ln=0)
                self.set_x(card_x + 14)
                self.set_font("Sans", "", 9)
                self.set_text_color(30, 30, 50)
                self.mcell(card_w - 20, 6, sent)
                self.ln(1)
        else:
            self.set_xy(card_x + 8, card_y + 8)
            self.mcell(card_w - 16, 7, content_clean)

        # ── Speaker notes strip ────────────────────────────────────────────────
        if speaker_note:
            notes_y  = H - 55
            notes_h  = 28
            # Notes background
            self.set_fill_color(20, 20, 40)
            self.rect(0, notes_y, W, notes_h, style="F")
            # Left accent bar
            self.set_fill_color(*acc)
            self.rect(0, notes_y, 3, notes_h, style="F")
            # Label
            self.set_xy(8, notes_y + 4)
            self.set_font("Sans", "B", 7)
            self.set_text_color(*acc)
            self.cell(30, 5, "SPEAKER NOTES", ln=0)
            # Note text
            self.set_xy(8, notes_y + 10)
            self.set_font("Sans", "I", 8)
            self.set_text_color(160, 160, 200)
            self.mcell(W - 16, 5, _safe(speaker_note)[:220])

        # ── Bottom bar & branding ──────────────────────────────────────────────
        self.set_fill_color(*acc)
        self.rect(0, H - 6, W, 6, style="F")
        self.set_xy(8, H - 14)
        self.set_font("Sans", "", 7)
        self.set_text_color(120, 120, 160)
        self.cell(W - 16, 5, f"LaunchForge AI  |  {SITE_URL}  |  {DATE_STR}", align="L", ln=0)

        # ── Restore normal mode ────────────────────────────────────────────────
        self._slide_mode = False
        self.set_auto_page_break(True, margin=18)
        self.set_margins(MARGIN, 10, MARGIN)


# ── Helpers ────────────────────────────────────────────────────────────────────
def _safe(val: Any, fallback: str = "-") -> str:
    """
    Convert any value to a string safe for fpdf2 with DejaVu fonts.
    Strips characters outside the Basic Multilingual Plane (emoji, etc.)
    that DejaVu does not cover.
    """
    if val is None:
        return fallback
    if isinstance(val, (dict, list)):
        import json
        s = json.dumps(val)[:200]
    else:
        s = str(val)
    # Remove characters outside BMP (emoji, flags, etc.) — DejaVu doesn't cover them
    s = "".join(c if ord(c) < 0x10000 else "?" for c in s)
    # Strip ASCII control characters
    s = "".join(c if ord(c) >= 32 or c in "\n\t" else "" for c in s)
    return s or fallback


def _list_of_str(val: Any) -> list[str]:
    if isinstance(val, list):
        return [str(v) for v in val]
    if isinstance(val, str):
        return [val]
    return []


# ══════════════════════════════════════════════════════════════════════════════
# 1 — Business Validation Report
# ══════════════════════════════════════════════════════════════════════════════
def generate_validation_pdf(data: dict, idea: str) -> bytes:
    pdf = _BasePDF("Business Validation Report", idea)
    pdf.page_title("Business Validation Report", idea)

    # Score card
    score = data.get("marketScore", "—")
    pdf.section_heading("Market Opportunity Score")
    pdf.set_font("Sans", "B", 36)
    pdf.set_text_color(*C_PURPLE)
    pdf.cell(0, 16, f"{score} / 100", align="C", ln=1)
    pdf.ln(2)

    # Key metrics
    pdf.section_heading("Market Sizing")
    for i, (k, v) in enumerate([
        ("TAM (Total Addressable Market)", data.get("tam", "—")),
        ("SAM (Serviceable Addressable)", data.get("sam", "—")),
        ("SOM (Obtainable Market)",        data.get("som", "—")),
    ]):
        pdf.kv_row(k, v, fill=(i % 2 == 0))
    pdf.ln(4)

    # Refined idea
    if data.get("refinedIdea"):
        pdf.section_heading("Refined Concept")
        pdf.body_text(data["refinedIdea"])

    # Problem / Solution / Target
    for field, label in [
        ("problemStatement", "Problem Statement"),
        ("targetAudience",   "Target Audience"),
        ("proposedSolution", "Proposed Solution"),
    ]:
        if data.get(field):
            pdf.sub_heading(label)
            pdf.body_text(data[field])

    # Competitors
    competitors = _list_of_str(data.get("competitors", []))
    if competitors:
        pdf.section_heading("Competitor Landscape")
        for c in competitors:
            pdf.bullet(c)
        pdf.ln(2)

    # Risk flags
    risks = _list_of_str(data.get("riskFlags", []))
    if risks:
        pdf.section_heading("Risk Flags")
        for r in risks:
            pdf.set_text_color(*C_RED)
            pdf.bullet(r, symbol="[!]")
        pdf.set_text_color(*C_DARK)
        pdf.ln(2)

    # Recommendation
    if data.get("recommendation"):
        pdf.section_heading("Recommendation")
        pdf.info_box(data["recommendation"], color=C_GREEN)

    return bytes(pdf.output())


# ══════════════════════════════════════════════════════════════════════════════
# 2 — Go-to-Market Strategy
# ══════════════════════════════════════════════════════════════════════════════
def generate_strategy_pdf(data: dict, idea: str) -> bytes:
    pdf = _BasePDF("GTM Strategy", idea)
    pdf.page_title("Go-to-Market Strategy", idea)

    # Positioning
    if data.get("competitivePositioning"):
        pdf.section_heading("Competitive Positioning")
        pdf.body_text(data["competitivePositioning"])

    # Monetisation
    if data.get("monetizationModel"):
        pdf.section_heading("Monetisation Model")
        pdf.body_text(data["monetizationModel"])

    # Pricing tiers
    pricing = data.get("pricingTiers", {})
    if isinstance(pricing, dict) and pricing:
        pdf.section_heading("Pricing Tiers")
        cols = [("Tier", 50), ("Price / Month", 60), ("Description", 72)]
        pdf.table_header(cols)
        for i, (tier, price) in enumerate(pricing.items()):
            row_val = price if isinstance(price, str) else str(price)
            pdf.table_row([(tier.capitalize(), 50), (row_val, 60), ("", 72)],
                          even=(i % 2 == 0))
        pdf.ln(4)

    # Target channels
    channels = _list_of_str(data.get("targetChannels", []))
    if channels:
        pdf.section_heading("Launch Channels")
        pdf.tag_pills(channels)

    # Launch timeline
    timeline = data.get("launchTimeline", {})
    if isinstance(timeline, dict) and timeline:
        pdf.section_heading("Launch Timeline")
        for i, (phase, desc) in enumerate(timeline.items()):
            pdf.kv_row(phase, str(desc), fill=(i % 2 == 0))
        pdf.ln(2)
    elif isinstance(timeline, list):
        pdf.section_heading("Launch Timeline")
        for item in timeline:
            pdf.bullet(str(item))
        pdf.ln(2)

    # Customer acquisition
    cac = data.get("customerAcquisition") or data.get("cacStrategy")
    if cac:
        pdf.section_heading("Customer Acquisition Strategy")
        pdf.body_text(str(cac))

    # Key metrics
    metrics = data.get("keyMetrics") or data.get("successMetrics")
    if isinstance(metrics, list):
        pdf.section_heading("Key Success Metrics")
        for m in metrics:
            pdf.bullet(str(m))

    return bytes(pdf.output())


# ══════════════════════════════════════════════════════════════════════════════
# 3 — Technical Architecture
# ══════════════════════════════════════════════════════════════════════════════
def generate_architecture_pdf(data: dict, idea: str) -> bytes:
    pdf = _BasePDF("Technical Architecture", idea)
    pdf.page_title("Technical Architecture", idea)

    # System design
    if data.get("systemDesign"):
        pdf.section_heading("System Design Overview")
        pdf.body_text(data["systemDesign"])

    # Tech stack
    stack = data.get("recommendedStack", {})
    if isinstance(stack, dict) and stack:
        pdf.section_heading("Recommended Tech Stack")
        cols = [("Layer", 55), ("Technology", 127)]
        pdf.table_header(cols)
        for i, (layer, tech) in enumerate(stack.items()):
            pdf.table_row([(layer.capitalize(), 55), (str(tech), 127)],
                          even=(i % 2 == 0))
        pdf.ln(4)

    # API endpoints
    endpoints = data.get("apiEndpoints", [])
    if isinstance(endpoints, list) and endpoints:
        pdf.section_heading("Key API Endpoints")
        cols = [("Method", 22), ("Path", 70), ("Description", 90)]
        pdf.table_header(cols)
        for i, ep in enumerate(endpoints[:20]):
            if isinstance(ep, dict):
                pdf.table_row([
                    (ep.get("method", "GET"), 22),
                    (ep.get("path", ""), 70),
                    (ep.get("description", ""), 90),
                ], even=(i % 2 == 0))
        pdf.ln(4)

    # Data models
    models = data.get("dataModels") or data.get("databaseSchema")
    if models:
        pdf.section_heading("Data Models")
        if isinstance(models, list):
            for m in models:
                pdf.bullet(str(m))
        else:
            pdf.body_text(str(models))

    # Scalability notes
    scaling = data.get("scalabilityNotes") or data.get("scalability")
    if scaling:
        pdf.section_heading("Scalability & Infrastructure")
        pdf.body_text(str(scaling))

    # Third-party integrations
    integrations = _list_of_str(data.get("thirdPartyIntegrations", []))
    if integrations:
        pdf.section_heading("Third-Party Integrations")
        pdf.tag_pills(integrations)

    return bytes(pdf.output())


# ══════════════════════════════════════════════════════════════════════════════
# 4 — Security Audit Report
# ══════════════════════════════════════════════════════════════════════════════
def generate_security_pdf(data: dict, idea: str) -> bytes:
    pdf = _BasePDF("Security Audit Report", idea)
    pdf.page_title("Security Audit Report", idea)

    # Badge
    if data.get("badge"):
        pdf.set_font("Sans", "B", 14)
        pdf.set_text_color(*C_GREEN)
        pdf.cell(0, 10, f"[SECURITY CLEARED]  {data['badge']}", align="C", ln=1)
        pdf.ln(2)

    # Overall score
    if data.get("overallScore") is not None:
        pdf.section_heading("Overall Security Score")
        pdf.set_font("Sans", "B", 32)
        pdf.set_text_color(*C_PURPLE)
        pdf.cell(0, 14, f"{data['overallScore']} / 100", align="C", ln=1)
        pdf.ln(2)

    # OWASP audit
    owasp = data.get("owaspAudit", [])
    if isinstance(owasp, list) and owasp:
        pdf.section_heading("OWASP Top 10 Audit")
        cols = [("ID", 18), ("Check", 65), ("Status", 22), ("Severity", 28), ("Recommendation", 49)]
        pdf.table_header(cols)
        for i, item in enumerate(owasp):
            if not isinstance(item, dict):
                continue
            status = str(item.get("status", "—"))
            severity = str(item.get("severity", "—"))
            color_before = pdf.get_y()
            # Draw row
            pdf.set_fill_color(*(C_ROW_EVEN if i % 2 == 0 else C_ROW_ODD))
            pdf.set_text_color(*pdf.severity_badge(status))
            pdf.set_font("Sans", "B", 7)
            pdf.cell(18, LINE_H + 1, _safe(item.get("id", "")), fill=True)
            pdf.set_text_color(*C_DARK)
            pdf.set_font("Sans", "", 7)
            pdf.cell(65, LINE_H + 1, _safe(item.get("name", ""))[:55], fill=True)
            pdf.set_text_color(*pdf.severity_badge(status))
            pdf.cell(22, LINE_H + 1, status, fill=True, align="C")
            pdf.set_text_color(*pdf.severity_badge(severity))
            pdf.cell(28, LINE_H + 1, severity, fill=True, align="C")
            pdf.set_text_color(*C_GRAY)
            pdf.cell(49, LINE_H + 1, _safe(item.get("fix", ""))[:45], fill=True, ln=1)
        pdf.ln(4)

    # Vulnerability details
    vulns = data.get("vulnerabilities") or data.get("criticalIssues", [])
    if isinstance(vulns, list) and vulns:
        pdf.section_heading("Vulnerability Details")
        for v in vulns:
            if isinstance(v, dict):
                sev = str(v.get("severity", ""))
                pdf.set_text_color(*pdf.severity_badge(sev))
                pdf.set_font("Sans", "B", 9)
                pdf.cell(0, LINE_H, f"[{sev}]  {_safe(v.get('name', v.get('title', '')))}",
                         ln=1)
                pdf.set_text_color(*C_DARK)
                pdf.set_font("Sans", "", 8)
                if v.get("description"):
                    pdf.mcell(0, LINE_H, _safe(v["description"]))
                if v.get("fix") or v.get("recommendation"):
                    fix = v.get("fix") or v.get("recommendation", "")
                    pdf.set_text_color(*C_GREEN)
                    pdf.mcell(0, LINE_H, f"Fix: {_safe(fix)}")
                    pdf.set_text_color(*C_DARK)
                pdf.ln(2)

    # Recommendations
    recs = _list_of_str(data.get("recommendations", []))
    if recs:
        pdf.section_heading("Recommendations")
        for r in recs:
            pdf.bullet(r, symbol="[+]")

    return bytes(pdf.output())


# ══════════════════════════════════════════════════════════════════════════════
# 5 — Marketing Kit (Copy + Pitch Deck)
# ══════════════════════════════════════════════════════════════════════════════
def generate_marketing_pdf(data: dict, idea: str) -> bytes:
    pdf = _BasePDF("Marketing & Launch Kit", idea)
    pdf.page_title("Marketing & Launch Kit", idea)

    # Taglines
    taglines = _list_of_str(data.get("taglines", []))
    if taglines:
        pdf.section_heading("Tagline Options")
        for i, t in enumerate(taglines, 1):
            pdf.set_font("Sans", "B", 11)
            pdf.set_text_color(*C_PURPLE)
            pdf.cell(8, 8, f"{i}.", ln=0)
            pdf.set_font("Sans", "", 11)
            pdf.set_text_color(*C_DARK)
            pdf.mcell(0, 8, t)
        pdf.ln(2)

    # Positioning statement
    if data.get("positioningStatement"):
        pdf.section_heading("Positioning Statement")
        pdf.info_box(data["positioningStatement"])

    # Hero section
    hero = data.get("heroSection", {})
    if isinstance(hero, dict) and hero:
        pdf.section_heading("Hero Section Copy")
        for i, (k, v) in enumerate(hero.items()):
            pdf.kv_row(k.capitalize(), str(v), fill=(i % 2 == 0))
        pdf.ln(4)

    # Features section
    features = data.get("featuresSection", [])
    if isinstance(features, list) and features:
        pdf.section_heading("Feature Descriptions")
        for f in features:
            if isinstance(f, dict):
                icon = _safe(f.get("icon", "*"))
                pdf.set_font("Sans", "B", 9)
                pdf.set_text_color(*C_PURPLE)
                pdf.cell(0, 6, f"{icon}  {_safe(f.get('title', ''))}", ln=1)
                pdf.set_font("Sans", "", 8)
                pdf.set_text_color(*C_GRAY)
                pdf.mcell(0, 5, _safe(f.get("description", "")))
                pdf.ln(1)
        pdf.ln(2)

    # Social proof
    proof = _list_of_str(data.get("socialProof", []))
    if proof:
        pdf.section_heading("Social Proof")
        for p in proof:
            pdf.bullet(p, symbol="*")
        pdf.ln(2)

    # Objection handlers
    objections = data.get("objectionHandlers", [])
    if isinstance(objections, list) and objections:
        pdf.section_heading("Objection Handlers")
        for obj in objections:
            if isinstance(obj, dict):
                pdf.set_font("Sans", "B", 9)
                pdf.set_text_color(*C_RED)
                pdf.mcell(0, 6, f"Q: {_safe(obj.get('objection', ''))}")
                pdf.set_font("Sans", "", 9)
                pdf.set_text_color(*C_GREEN)
                pdf.mcell(0, 6, f"A: {_safe(obj.get('response', ''))}")
                pdf.ln(1)
        pdf.ln(2)

    # Product Hunt + meta
    if data.get("productHuntTagline"):
        pdf.section_heading("Product Hunt Tagline")
        pdf.info_box(data["productHuntTagline"])
    if data.get("metaDescription"):
        pdf.section_heading("Meta Description")
        pdf.body_text(data["metaDescription"])

    # Email sequence
    emails = data.get("emailSequence", [])
    if isinstance(emails, list) and emails:
        pdf.section_heading("Email Sequence")
        for i, em in enumerate(emails, 1):
            if isinstance(em, dict):
                pdf.set_font("Sans", "B", 9)
                pdf.set_text_color(*C_PURPLE)
                pdf.cell(0, 6, f"Email {i}: {_safe(em.get('subject', ''))}", ln=1)
                pdf.set_font("Sans", "I", 8)
                pdf.set_text_color(*C_GRAY)
                pdf.cell(0, 5, f"Preview: {_safe(em.get('preview', ''))}", ln=1)
                pdf.set_font("Sans", "", 8)
                pdf.set_text_color(*C_DARK)
                pdf.mcell(0, 5, _safe(em.get("body", "")))
                pdf.ln(2)

    # ── Pitch Deck — each slide gets a beautiful full page ──────────────────
    slides = data.get("pitchDeck", [])
    valid_slides = [s for s in slides if isinstance(s, dict)] if isinstance(slides, list) else []
    if valid_slides:
        # Transition page — "Investor Pitch Deck" cover
        pdf.add_page()
        pdf.set_fill_color(*C_NAVY)
        pdf.rect(0, 0, 210, 297, style="F")
        pdf.set_fill_color(*C_PURPLE)
        pdf.rect(0, 0, 4, 297, style="F")
        pdf.rect(206, 0, 4, 297, style="F")
        pdf.rect(0, 0, 210, 4, style="F")
        pdf.rect(0, 293, 210, 4, style="F")
        pdf.set_xy(14, 110)
        pdf.set_font("Sans", "B", 8)
        pdf.set_text_color(*C_PURPLE_LT)
        pdf.cell(182, 8, "INVESTOR PITCH DECK", align="C", ln=1)
        pdf.set_xy(14, 122)
        pdf.set_font("Sans", "B", 32)
        pdf.set_text_color(*C_WHITE)
        pdf.mcell(182, 14, "LaunchForge AI", align="C")
        pdf.set_xy(14, pdf.get_y() + 4)
        pdf.set_font("Sans", "", 12)
        pdf.set_text_color(167, 119, 248)
        pdf.mcell(182, 8, _safe(idea[:70]), align="C")
        pdf.set_fill_color(*C_PURPLE)
        pdf.rect(65, pdf.get_y() + 6, 80, 2, style="F")
        pdf.set_xy(14, pdf.get_y() + 16)
        pdf.set_font("Sans", "", 9)
        pdf.set_text_color(100, 100, 140)
        pdf.mcell(182, 6, f"{len(valid_slides)}-Slide Deck  |  {DATE_STR}", align="C")
        pdf.set_fill_color(*C_PURPLE)
        pdf.rect(0, 293, 210, 4, style="F")

        # Individual slides
        for slide in valid_slides:
            pdf.draw_slide_page(
                slide_num    = int(slide.get("slide", 1)),
                total        = len(valid_slides),
                title        = str(slide.get("title", "")),
                content      = str(slide.get("content", "")),
                speaker_note = str(slide.get("speakerNote", "")),
            )

    return bytes(pdf.output())


# ══════════════════════════════════════════════════════════════════════════════
# 6 — SEO Strategy
# ══════════════════════════════════════════════════════════════════════════════
def generate_seo_pdf(data: dict, idea: str) -> bytes:
    pdf = _BasePDF("SEO Strategy", idea)
    pdf.page_title("SEO Strategy", idea)

    # Meta tags
    meta = data.get("metaTags", {})
    if isinstance(meta, dict) and meta:
        pdf.section_heading("Meta Tags")
        for i, (k, v) in enumerate(meta.items()):
            pdf.kv_row(k, str(v), fill=(i % 2 == 0))
        pdf.ln(4)

    # Monthly search volume
    if data.get("estimatedMonthlySearchVolume"):
        pdf.section_heading("Estimated Monthly Search Volume")
        pdf.set_font("Sans", "B", 18)
        pdf.set_text_color(*C_PURPLE)
        pdf.cell(0, 10, str(data["estimatedMonthlySearchVolume"]),
                 align="C", ln=1)
        pdf.ln(2)

    # Primary keywords
    primary = data.get("primaryKeywords", [])
    if isinstance(primary, list) and primary:
        pdf.section_heading("Primary Keywords")
        # Try to render as table if objects
        if isinstance(primary[0], dict):
            cols = [("Keyword", 70), ("Volume", 40), ("Difficulty", 40), ("Intent", 32)]
            pdf.table_header(cols)
            for i, kw in enumerate(primary[:25]):
                pdf.table_row([
                    (str(kw.get("keyword", kw.get("term", ""))), 70),
                    (str(kw.get("estimatedVolume", kw.get("volume", "—"))), 40),
                    (str(kw.get("difficulty", "—")), 40),
                    (str(kw.get("intent", "—")), 32),
                ], even=(i % 2 == 0))
            pdf.ln(4)
        else:
            pdf.tag_pills([str(k) for k in primary])

    # Long-tail keywords
    longtail = data.get("longTailKeywords", [])
    if isinstance(longtail, list) and longtail:
        pdf.section_heading("Long-tail Keywords")
        labels = []
        for k in longtail:
            if isinstance(k, dict):
                labels.append(str(k.get("keyword", k.get("term", str(k)))))
            else:
                labels.append(str(k))
        pdf.tag_pills(labels)

    # Content strategy
    content_strat = data.get("contentStrategy", [])
    if isinstance(content_strat, list) and content_strat:
        pdf.section_heading("Content Strategy")
        for item in content_strat:
            if isinstance(item, dict):
                pdf.bullet(f"{item.get('topic', item.get('title', ''))} — {item.get('type', item.get('format', ''))}")
            else:
                pdf.bullet(str(item))
        pdf.ln(2)

    # Link building
    link = data.get("linkBuildingStrategy") or data.get("backlinkStrategy")
    if link:
        pdf.section_heading("Link Building Strategy")
        if isinstance(link, list):
            for l in link:
                pdf.bullet(str(l))
        else:
            pdf.body_text(str(link))

    # Technical SEO
    tech_seo = data.get("technicalSEO") or data.get("technicalRecommendations")
    if tech_seo:
        pdf.section_heading("Technical SEO Recommendations")
        if isinstance(tech_seo, list):
            for t in tech_seo:
                pdf.bullet(str(t))
        else:
            pdf.body_text(str(tech_seo))

    return bytes(pdf.output())


# ══════════════════════════════════════════════════════════════════════════════
# 7 — MVP Code Report
# ══════════════════════════════════════════════════════════════════════════════
def generate_mvp_code_pdf(data: dict, idea: str) -> bytes:
    pdf = _BasePDF("MVP Code Overview", idea)
    pdf.page_title("Generated MVP Code", idea)

    if data.get("readmeSummary"):
        pdf.section_heading("README Summary")
        pdf.body_text(data["readmeSummary"])

    if data.get("techStack"):
        pdf.section_heading("Tech Stack")
        pdf.body_text(str(data["techStack"]))

    # Setup instructions
    setup = _list_of_str(data.get("setupInstructions", []))
    if setup:
        pdf.section_heading("Setup Instructions")
        for i, step in enumerate(setup, 1):
            pdf.bullet(step, symbol=f"{i}.")
        pdf.ln(2)

    # Env variables
    env_vars = _list_of_str(data.get("envVariables", []))
    if env_vars:
        pdf.section_heading("Environment Variables (.env.example)")
        pdf.code_block("\n".join(env_vars))

    # File listing
    files = data.get("files", [])
    if isinstance(files, list) and files:
        pdf.section_heading("Generated Files")
        cols = [("File Path", 90), ("Description", 92)]
        pdf.table_header(cols)
        for i, f in enumerate(files[:30]):
            if isinstance(f, dict):
                pdf.table_row([
                    (str(f.get("path", "")), 90),
                    (str(f.get("description", ""))[:80], 92),
                ], even=(i % 2 == 0))
        pdf.ln(4)

        # Show first 3 files' code
        pdf.section_heading("Code Snippets (First 3 Files)")
        for f in files[:3]:
            if isinstance(f, dict) and f.get("content"):
                pdf.sub_heading(str(f.get("path", "file")))
                pdf.code_block(str(f["content"]), max_lines=25)

    return bytes(pdf.output())


# ══════════════════════════════════════════════════════════════════════════════
# Public entry-point
# ══════════════════════════════════════════════════════════════════════════════
SECTION_MAP = {
    "idea_validator":   ("01_business_validation.pdf",    generate_validation_pdf),
    "strategy_planner": ("02_gtm_strategy.pdf",           generate_strategy_pdf),
    "product_architect":("03_technical_architecture.pdf", generate_architecture_pdf),
    "security_reviewer":("04_security_audit.pdf",         generate_security_pdf),
    "copywriter":       ("05_marketing_kit.pdf",          generate_marketing_pdf),
    "seo_optimizer":    ("06_seo_strategy.pdf",           generate_seo_pdf),
    "code_generator":   ("07_mvp_code_overview.pdf",      generate_mvp_code_pdf),
}


def build_all_pdfs(agents: dict, idea: str) -> list[tuple[str, bytes]]:
    """
    Generate PDFs for every completed agent.

    Returns a list of (filename, pdf_bytes) tuples ready to zip.
    """
    results = []
    for agent_id, (filename, generator) in SECTION_MAP.items():
        ag = agents.get(agent_id, {})
        if ag.get("status") not in ("complete", "completed"):
            continue
        result_data = ag.get("result", {})
        if not result_data:
            continue
        try:
            pdf_bytes = generator(result_data, idea)
            results.append((filename, pdf_bytes))
        except Exception as exc:
            import logging
            logging.getLogger(__name__).warning(
                f"PDF generation failed for {agent_id}: {exc}"
            )
    return results
