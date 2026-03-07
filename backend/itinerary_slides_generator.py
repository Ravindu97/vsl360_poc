"""
Premium itinerary slide generator – VSL 360.

Design pillars:
  • Full-bleed imagery with cinematic gradient overlays
  • Generous white-space, editorial typography (mixed weights)
  • Gold / charcoal luxury palette with subtle warm neutrals
  • Layered depth: semi-transparent panels, thin accent lines,
    decorative geometric elements
  • Magazine-style alternating day layouts
"""

from datetime import datetime
import base64
import io
import mimetypes
import os
from typing import Dict, List, Optional, Tuple

import requests
from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_AUTO_SHAPE_TYPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt, Emu

from image_generator import auto_populate_images

# ── constants ────────────────────────────────────────────────────────────────
W, H = 13.33, 7.5  # widescreen dims (inches)

LOCAL_IMAGE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sample_itinerary", "images")
)

# ── colour palettes ─────────────────────────────────────────────────────────
THEMES = {
    "modern_luxe": {
        "bg":          RGBColor(250, 249, 247),   # warm off-white
        "ink":         RGBColor(28, 28, 30),       # near-black
        "sub":         RGBColor(72, 72, 74),       # dark grey
        "muted":       RGBColor(142, 142, 147),    # mid grey
        "accent":      RGBColor(183, 149, 93),     # warm gold
        "accent_dark": RGBColor(140, 109, 60),     # deep gold
        "accent_light":RGBColor(232, 218, 192),    # pale gold
        "line":        RGBColor(225, 221, 214),     # warm rule
        "panel":       RGBColor(255, 255, 255),
        "panel_alt":   RGBColor(245, 243, 240),    # tinted card
        "overlay_dark":RGBColor(18, 18, 20),
        "success":     RGBColor(52, 140, 98),
        "danger":      RGBColor(196, 69, 69),
        "serif":       "Georgia",
        "sans":        "Segoe UI",
    },
    "editorial_bold": {
        "bg":          RGBColor(248, 246, 240),
        "ink":         RGBColor(38, 34, 31),
        "sub":         RGBColor(82, 75, 68),
        "muted":       RGBColor(145, 136, 125),
        "accent":      RGBColor(183, 134, 62),
        "accent_dark": RGBColor(131, 86, 35),
        "accent_light":RGBColor(239, 224, 199),
        "line":        RGBColor(220, 212, 200),
        "panel":       RGBColor(255, 252, 248),
        "panel_alt":   RGBColor(247, 244, 238),
        "overlay_dark":RGBColor(24, 20, 16),
        "success":     RGBColor(74, 140, 91),
        "danger":      RGBColor(181, 74, 74),
        "serif":       "Georgia",
        "sans":        "Segoe UI",
    },
}

# ── image helpers ────────────────────────────────────────────────────────────

def _resolve_image_source_to_local(source: str) -> Tuple[Optional[str], bool]:
    if not source:
        return None, False
    normalized = source.strip()
    if normalized.startswith(("http://", "https://")):
        return None, False
    candidates = []
    if os.path.isabs(normalized):
        candidates.append(normalized)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
        candidates.append(os.path.join(LOCAL_IMAGE_DIR, normalized))
        candidates.append(os.path.abspath(os.path.join(base, "..", normalized)))
        candidates.append(os.path.abspath(os.path.join(base, normalized)))
    for c in candidates:
        if os.path.isfile(c):
            return c, False
    return None, False


def _load_image_bytes(source: Optional[str]) -> Optional[bytes]:
    if not source:
        return None
    try:
        if source.startswith("data:image"):
            _, encoded = source.split(",", 1)
            return base64.b64decode(encoded)
        if source.startswith(("http://", "https://")):
            r = requests.get(source, timeout=20)
            r.raise_for_status()
            return r.content
        local, _ = _resolve_image_source_to_local(source)
        if local:
            with open(local, "rb") as f:
                return f.read()
    except Exception:
        return None
    return None


def _to_pptx_compatible_image_stream(image_bytes: bytes) -> io.BytesIO:
    with Image.open(io.BytesIO(image_bytes)) as img:
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGB")
        out = io.BytesIO()
        img.save(out, format="PNG")
        out.seek(0)
        return out


# ── low-level drawing primitives ─────────────────────────────────────────────

def _rect(slide, left, top, width, height, fill: RGBColor,
          line_rgb: Optional[RGBColor] = None, rounded=False, transparency: Optional[int] = None):
    """Draw a rectangle. *transparency* 0-100 (percent)."""
    from lxml import etree
    st = MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE if rounded else MSO_AUTO_SHAPE_TYPE.RECTANGLE
    shape = slide.shapes.add_shape(st, Inches(left), Inches(top), Inches(width), Inches(height))
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    if transparency is not None:
        # Inject alpha into the XML: spPr > solidFill > srgbClr > a:alpha
        sp_pr = shape._element.spPr
        solid_fill_elem = sp_pr.find(qn('a:solidFill'))
        if solid_fill_elem is not None:
            clr_elem = solid_fill_elem.find(qn('a:srgbClr'))
            if clr_elem is not None:
                alpha_elem = clr_elem.find(qn('a:alpha'))
                if alpha_elem is None:
                    alpha_elem = etree.SubElement(clr_elem, qn('a:alpha'))
                alpha_elem.set('val', str((100 - transparency) * 1000))
    if line_rgb:
        shape.line.color.rgb = line_rgb
        shape.line.width = Pt(0.75)
    else:
        shape.line.fill.background()
    return shape


def _thin_line(slide, left, top, width, color: RGBColor, thickness=0.02):
    """Ultra-thin horizontal rule."""
    return _rect(slide, left, top, width, thickness, color)


def _text(slide, text: str, left, top, width, height,
          size=24, color: Optional[RGBColor] = None, bold=False,
          align=PP_ALIGN.LEFT, font="Segoe UI", italic=False,
          spacing: Optional[float] = None, anchor=MSO_ANCHOR.TOP):
    """Add a text box with fine-grained control."""
    box = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = box.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    p = tf.paragraphs[0]
    p.text = text
    p.alignment = align
    if spacing is not None:
        p.space_after = Pt(spacing)
    run = p.runs[0]
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.name = font
    run.font.italic = italic
    if color:
        run.font.color.rgb = color
    return box


def _multiline_text(slide, lines: List[str], left, top, width, height,
                    size=13, color: Optional[RGBColor] = None, font="Segoe UI",
                    line_spacing: float = 1.15, bold=False, align=PP_ALIGN.LEFT):
    """Text box with explicit line breaks and controlled leading."""
    box = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = box.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.TOP
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = line
        p.alignment = align
        p.space_before = Pt(0)
        p.space_after = Pt(size * (line_spacing - 1))
        for run in p.runs:
            run.font.size = Pt(size)
            run.font.name = font
            run.font.bold = bold
            if color:
                run.font.color.rgb = color
    return box


def _picture(slide, source: Optional[str], left, top, width, height) -> bool:
    """Place an image; returns True on success."""
    raw = _load_image_bytes(source)
    if not raw:
        return False
    try:
        stream = _to_pptx_compatible_image_stream(raw)
        slide.shapes.add_picture(stream, Inches(left), Inches(top), Inches(width), Inches(height))
        return True
    except Exception:
        return False


def _circle(slide, cx, cy, r, fill: RGBColor, line_rgb: Optional[RGBColor] = None):
    """Small decorative circle (centred on cx, cy)."""
    shape = slide.shapes.add_shape(
        MSO_AUTO_SHAPE_TYPE.OVAL,
        Inches(cx - r), Inches(cy - r), Inches(2 * r), Inches(2 * r),
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    if line_rgb:
        shape.line.color.rgb = line_rgb
        shape.line.width = Pt(1)
    else:
        shape.line.fill.background()
    return shape


# ── theme selector ───────────────────────────────────────────────────────────

def _pick_theme(template_name: Optional[str]) -> dict:
    name = (template_name or "modern_luxe").lower()
    if "editorial" in name or "bold" in name:
        return THEMES["editorial_bold"]
    return THEMES["modern_luxe"]


def _safe_list(data, key: str):
    v = data.get(key, [])
    return v if isinstance(v, list) else []


# ═══════════════════════════════════════════════════════════════════════════════
#  S L I D E   B U I L D E R S
# ═══════════════════════════════════════════════════════════════════════════════

def _add_cover_slide(prs, trip_data, t):
    """Full-bleed cinematic cover with layered gradient overlay."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    # Full-bleed background image
    src = trip_data.get("cover_image_path") or trip_data.get("cover_image_url")
    if not _picture(slide, src, 0, 0, W, H):
        _rect(slide, 0, 0, W, H, t["overlay_dark"])

    # Multi-layer gradient: darker at bottom for text legibility
    _rect(slide, 0, 0, W, H, RGBColor(0, 0, 0), transparency=50)
    _rect(slide, 0, 4.0, W, 3.5, RGBColor(0, 0, 0), transparency=30)

    # Thin gold accent line across top
    _rect(slide, 0, 0, W, 0.06, t["accent"])

    # Brand mark — top-left
    _text(slide, "VSL 360", 0.9, 0.5, 3, 0.45, 13, t["accent"], True, font=t["sans"],
          spacing=6)
    _text(slide, "T R A V E L  I T I N E R A R Y", 0.92, 0.88, 5, 0.3, 9.5,
          RGBColor(210, 210, 210), False, font=t["sans"], spacing=0)

    # Decorative thin line under brand
    _thin_line(slide, 0.92, 1.22, 1.6, t["accent"])

    # Trip title — large serif for editorial feel
    _text(slide, trip_data.get("trip_name", "Travel Itinerary"),
          0.9, 2.8, 8.5, 1.6, 54, RGBColor(255, 255, 255), True,
          font=t["serif"])

    # Country subtitle
    country = trip_data.get("destination_country", "")
    if country:
        _text(slide, country.upper(), 0.95, 4.55, 5, 0.5, 18,
              RGBColor(220, 215, 205), False, font=t["sans"], italic=True,
              spacing=4)

    # Decorative gold thin line under title block
    _thin_line(slide, 0.92, 5.2, 3.5, t["accent"])

    # Duration badge — bottom-right, frosted panel style
    _rect(slide, 10.1, 5.5, 2.6, 1.3, RGBColor(0, 0, 0), t["accent"], rounded=True, transparency=40)
    nights = trip_data.get("total_nights", 0)
    days = trip_data.get("total_days", 0)
    _text(slide, str(nights), 10.1, 5.55, 2.6, 0.65, 36, RGBColor(255, 255, 255), True,
          PP_ALIGN.CENTER, font=t["serif"])
    _text(slide, f"NIGHTS  /  {days} DAYS", 10.1, 6.15, 2.6, 0.35, 9.5,
          t["accent_light"], False, PP_ALIGN.CENTER, font=t["sans"])

    # Customer name (if provided) — bottom-left
    cust = trip_data.get("customer_name")
    if cust:
        _text(slide, f"Prepared for {cust}", 0.92, 6.65, 6, 0.35, 12,
              RGBColor(200, 200, 200), False, font=t["sans"], italic=True)


def _add_overview_slide(prs, trip_data, t):
    """Two-column editorial overview with decorative accents."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _rect(slide, 0, 0, W, H, t["bg"])

    # Decorative vertical gold stripe on left edge
    _rect(slide, 0, 0, 0.06, H, t["accent"])

    # Section label
    _text(slide, "OVERVIEW", 0.9, 0.6, 4, 0.35, 10, t["muted"], True, font=t["sans"])
    _thin_line(slide, 0.9, 0.97, 1.2, t["accent"])

    # Title
    _text(slide, "Your Journey", 0.9, 1.2, 6, 0.65, 38, t["ink"], True, font=t["serif"])

    # Overview paragraph — left column
    overview = trip_data.get("overview_text", "") or \
        "A carefully curated journey through breathtaking landscapes and rich cultural heritage."
    _text(slide, overview, 0.9, 2.2, 6.8, 4.0, 15, t["sub"], False, font=t["sans"])

    # Dates line
    start = trip_data.get("start_date", "")
    end = trip_data.get("end_date", "")
    if start and end:
        _text(slide, f"{start}  —  {end}", 0.9, 6.4, 5, 0.35, 12, t["muted"], False,
              font=t["sans"], italic=True)

    # Right panel — frosted card with location summary
    _rect(slide, 8.4, 0.55, 4.35, 6.4, t["panel"], t["line"], rounded=True)
    # Gold bar at top of card
    _rect(slide, 8.4, 0.55, 4.35, 0.08, t["accent"])
    _text(slide, "DESTINATIONS", 8.8, 1.0, 3.5, 0.35, 10, t["accent_dark"], True,
          font=t["sans"])
    _thin_line(slide, 8.8, 1.38, 2.0, t["line"])

    y = 1.7
    for item in _safe_list(trip_data, "location_summary")[:8]:
        city = item.get("city", "")
        nights = item.get("nights", 0)
        # Gold circle bullet
        _circle(slide, 9.0, y + 0.13, 0.06, t["accent"])
        _text(slide, city, 9.2, y, 2.5, 0.32, 15, t["ink"], True, font=t["sans"])
        _text(slide, f"{nights} night{'s' if nights != 1 else ''}", 11.6, y, 1.0, 0.32,
              12, t["muted"], False, PP_ALIGN.RIGHT, font=t["sans"])
        y += 0.52

    # Total at bottom of card
    _thin_line(slide, 8.8, y + 0.15, 3.55, t["line"])
    _text(slide, f"{trip_data.get('total_nights', 0)} Nights  |  {trip_data.get('total_days', 0)} Days",
          8.8, y + 0.35, 3.55, 0.35, 13, t["accent_dark"], True, PP_ALIGN.CENTER, font=t["sans"])


def _add_route_slide(prs, trip_data, t):
    """Elegant horizontal timeline with connected nodes."""
    days = _safe_list(trip_data, "days")
    if not days:
        return

    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _rect(slide, 0, 0, W, H, t["panel"])

    # Decorative top line
    _rect(slide, 0, 0, W, 0.06, t["accent"])

    _text(slide, "ROUTE", 0.9, 0.55, 3, 0.3, 10, t["muted"], True, font=t["sans"])
    _thin_line(slide, 0.9, 0.88, 1.0, t["accent"])
    _text(slide, "At a Glance", 0.9, 1.05, 5, 0.6, 36, t["ink"], True, font=t["serif"])

    # Extract unique consecutive cities
    stops = []
    for d in days:
        city = (d.get("city") or "").strip()
        if city and (not stops or stops[-1] != city):
            stops.append(city)
    if not stops:
        stops = ["Start", "Destination"]
    max_n = 7
    if len(stops) > max_n:
        stops = stops[:max_n - 1] + [stops[-1]]

    # Timeline
    rail_y = 3.7
    rail_left = 1.4
    rail_right = 11.9
    rail_w = rail_right - rail_left

    # Connector line
    _thin_line(slide, rail_left, rail_y + 0.08, rail_w, t["line"], thickness=0.03)

    spacing = rail_w / max(1, len(stops) - 1)
    for i, city in enumerate(stops):
        cx = rail_left + i * spacing
        # Outer ring
        _circle(slide, cx, rail_y + 0.09, 0.14, t["panel"], t["accent"])
        # Inner dot
        _circle(slide, cx, rail_y + 0.09, 0.07, t["accent"])
        # City label below
        _text(slide, city, cx - 0.75, rail_y + 0.45, 1.5, 0.42, 12, t["ink"], True,
              PP_ALIGN.CENTER, font=t["sans"])
        # Day number above
        _text(slide, f"Day {i + 1}" if i < len(days) else "",
              cx - 0.5, rail_y - 0.45, 1.0, 0.35, 9, t["muted"], False,
              PP_ALIGN.CENTER, font=t["sans"])

    # Summary bar at bottom
    _rect(slide, 0.9, 5.8, 11.5, 1.0, t["panel_alt"], t["line"], rounded=True)
    summary_lines = [
        f"{trip_data.get('total_days', 0)} days  •  {trip_data.get('total_nights', 0)} nights",
        "Curated experiences across each destination",
    ]
    _multiline_text(slide, summary_lines, 1.2, 5.95, 11.0, 0.8, 13, t["muted"],
                    font=t["sans"], line_spacing=1.5, align=PP_ALIGN.CENTER)


def _add_day_slide(prs, day, idx, t):
    """Clean split layout — image on one side, content on the other."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    left_image = idx % 2 == 0
    img_src = day.get("image_path") or day.get("image_url")

    # Simple 50/50 split
    split = 6.66
    if left_image:
        img_x, img_w = 0, split
        content_x, content_w = split + 0.5, W - split - 0.9
    else:
        img_x, img_w = W - split, split
        content_x, content_w = 0.7, W - split - 0.9

    # White background for whole slide
    _rect(slide, 0, 0, W, H, t["panel"])

    # Image or placeholder
    placed = _picture(slide, img_src, img_x, 0, img_w, H) if img_src else False
    if not placed:
        _rect(slide, img_x, 0, img_w, H, t["panel_alt"])
        cx = img_x + img_w / 2
        _text(slide, "— image —", cx - 0.8, 3.5, 1.6, 0.3, 11, t["muted"],
              False, PP_ALIGN.CENTER, font=t["sans"], italic=True)

    # Thin gold vertical divider at the split edge
    div_x = split if left_image else (W - split)
    _rect(slide, div_x - 0.02, 0, 0.04, H, t["accent"])

    # Gold top bar
    _rect(slide, 0, 0, W, 0.04, t["accent"])

    # ── Header ──
    day_num = day.get("day", idx + 1)

    _rect(slide, content_x, 0.7, 0.58, 0.58, t["accent"], rounded=True)
    _text(slide, str(day_num), content_x, 0.7, 0.58, 0.58, 22,
          RGBColor(255, 255, 255), True, PP_ALIGN.CENTER, font=t["serif"],
          anchor=MSO_ANCHOR.MIDDLE)

    _text(slide, "DAY", content_x + 0.72, 0.7, 0.5, 0.24, 10,
          t["muted"], True, font=t["sans"])
    city = day.get("city", "")
    if city:
        _text(slide, city.upper(), content_x + 0.72, 0.94, content_w - 0.72,
              0.26, 11, t["accent_dark"], True, font=t["sans"])

    # Title
    _text(slide, day.get("title", "Untitled Day"), content_x, 1.5, content_w,
          0.8, 26, t["ink"], True, font=t["serif"])

    _thin_line(slide, content_x, 2.35, 2.0, t["accent"])

    # Activities
    activities = day.get("activities", []) or []
    ay = 2.65
    for act in activities[:7]:
        desc = (act.get("description") or "").strip() or "Activity"
        time_s = (act.get("time") or "").strip()
        if time_s:
            _text(slide, f"{time_s}  —  {desc}", content_x, ay, content_w, 0.32,
                  13, t["sub"], False, font=t["sans"])
        else:
            _circle(slide, content_x + 0.08, ay + 0.12, 0.04, t["accent"])
            _text(slide, desc, content_x + 0.25, ay, content_w - 0.25, 0.32,
                  13, t["sub"], False, font=t["sans"])
        ay += 0.42

    # Bottom stats
    _thin_line(slide, content_x, 6.25, content_w, t["line"])
    parts = []
    tt = day.get("travel_time")
    if tt and tt != "N/A":
        parts.append(f"Travel: {tt}")
    dist = day.get("distance")
    if dist and dist != "N/A":
        parts.append(f"Distance: {dist}")
    overnight = day.get("overnight_city") or day.get("city")
    if overnight:
        parts.append(f"Overnight: {overnight}")
    if parts:
        _text(slide, "   •   ".join(parts), content_x, 6.4, content_w, 0.28,
              10, t["muted"], False, font=t["sans"])

    optional = day.get("optional")
    if optional:
        _text(slide, f"Optional: {optional}", content_x, 6.75, content_w, 0.28, 10,
              t["accent_dark"], False, font=t["sans"], italic=True)


def _add_hotels_slide(prs, trip_data, t):
    """Elegant accommodation table with alternating row tint."""
    hotels = _safe_list(trip_data, "hotels")
    if not hotels:
        return

    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _rect(slide, 0, 0, W, H, t["bg"])
    _rect(slide, 0, 0, W, 0.045, t["accent"])

    # Decorative vertical gold stripe
    _rect(slide, 0, 0, 0.06, H, t["accent"])

    _text(slide, "ACCOMMODATION", 0.9, 0.5, 4, 0.3, 10, t["muted"], True, font=t["sans"])
    _thin_line(slide, 0.9, 0.83, 1.5, t["accent"])
    _text(slide, "Where You'll Stay", 0.9, 1.0, 7, 0.6, 36, t["ink"], True, font=t["serif"])

    # Column headers — adjusted positions to prevent Night(s) clipping
    header_y = 1.95
    _text(slide, "Property", 1.2, header_y, 4.0, 0.3, 10, t["muted"], True, font=t["sans"])
    _text(slide, "Location", 5.5, header_y, 2.0, 0.3, 10, t["muted"], True, font=t["sans"])
    _text(slide, "Room Type", 7.8, header_y, 2.5, 0.3, 10, t["muted"], True, font=t["sans"])
    _text(slide, "Nights", 10.5, header_y, 1.8, 0.3, 10, t["muted"], True, PP_ALIGN.RIGHT, font=t["sans"])
    _thin_line(slide, 0.85, 2.28, 11.5, t["line"])

    y = 2.45
    row_h = 0.75
    for i, hotel in enumerate(hotels[:7]):
        row_bg = t["panel_alt"] if i % 2 == 0 else t["panel"]
        _rect(slide, 0.8, y, 11.55, row_h, row_bg, rounded=True)
        # Gold accent dot
        _circle(slide, 1.05, y + row_h / 2, 0.055, t["accent"])
        _text(slide, hotel.get("name", "Hotel"), 1.25, y + 0.18, 4.0, 0.4, 14, t["ink"], True, font=t["sans"])
        _text(slide, hotel.get("city", ""), 5.5, y + 0.2, 2.0, 0.35, 13, t["sub"], False, font=t["sans"])
        _text(slide, hotel.get("room_type", ""), 7.8, y + 0.2, 2.5, 0.35, 12, t["muted"], False, font=t["sans"])
        _text(slide, hotel.get("night", ""), 10.5, y + 0.2, 1.8, 0.35, 13, t["accent_dark"], True,
              PP_ALIGN.RIGHT, font=t["sans"])
        y += row_h + 0.08


def _add_inclusions_slide(prs, trip_data, t):
    """Split panel with elegant include / exclude lists."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _rect(slide, 0, 0, W, H, t["panel"])
    _rect(slide, 0, 0, W, 0.045, t["accent"])

    # Decorative vertical gold stripe
    _rect(slide, 0, 0, 0.06, H, t["accent"])

    _text(slide, "PACKAGE DETAILS", 0.9, 0.5, 4, 0.3, 10, t["muted"], True, font=t["sans"])
    _thin_line(slide, 0.9, 0.83, 1.5, t["accent"])
    _text(slide, "What's Included", 0.9, 1.0, 7, 0.6, 36, t["ink"], True, font=t["serif"])

    # Left card — Included
    card_top = 1.85
    card_h = 4.95
    left_w = 5.65
    right_x = 6.7
    right_w = 5.75

    _rect(slide, 0.8, card_top, left_w, card_h, t["panel_alt"], t["line"], rounded=True)
    # Thin accent bar (not heavy block)
    _thin_line(slide, 0.8, card_top + 0.005, left_w, t["success"], thickness=0.035)
    _text(slide, "INCLUDED", 1.15, card_top + 0.25, 4, 0.3, 10, t["success"], True, font=t["sans"])
    _thin_line(slide, 1.15, card_top + 0.58, 1.5, t["line"])

    y = card_top + 0.78
    for item in _safe_list(trip_data, "tour_includes")[:12]:
        _circle(slide, 1.25, y + 0.11, 0.045, t["success"])
        _text(slide, item, 1.45, y, 4.75, 0.28, 12, t["sub"], False, font=t["sans"])
        y += 0.33

    # Right card — Excluded
    _rect(slide, right_x, card_top, right_w, card_h, t["panel_alt"], t["line"], rounded=True)
    _thin_line(slide, right_x, card_top + 0.005, right_w, t["danger"], thickness=0.035)
    _text(slide, "NOT INCLUDED", right_x + 0.35, card_top + 0.25, 4, 0.3, 10, t["danger"], True, font=t["sans"])
    _thin_line(slide, right_x + 0.35, card_top + 0.58, 1.5, t["line"])

    y = card_top + 0.78
    for item in _safe_list(trip_data, "tour_excludes")[:12]:
        _circle(slide, right_x + 0.25, y + 0.11, 0.045, t["danger"])
        _text(slide, item, right_x + 0.45, y, right_w - 0.7, 0.28, 12, t["sub"], False, font=t["sans"])
        y += 0.33

    # Cost badge at bottom — centred
    cost = trip_data.get("cost_per_person")
    if cost:
        badge_w = 5.0
        badge_x = (W - badge_w) / 2
        _rect(slide, badge_x, 7.0, badge_w, 0.42, t["accent"], rounded=True)
        _text(slide, f"Investment Per Person:  {cost}", badge_x, 7.02, badge_w, 0.38, 13,
              RGBColor(255, 255, 255), True, PP_ALIGN.CENTER, font=t["sans"])


def _add_closing_slide(prs, trip_data, t):
    """Cinematic closing slide with full-bleed image or dark fill."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    # Try cover image again for visual consistency
    src = trip_data.get("cover_image_path") or trip_data.get("cover_image_url")
    if not _picture(slide, src, 0, 0, W, H):
        _rect(slide, 0, 0, W, H, t["overlay_dark"])

    _rect(slide, 0, 0, W, H, RGBColor(0, 0, 0), transparency=40)
    _rect(slide, 0, 0, W, 0.05, t["accent"])

    # Elegant centred content
    _thin_line(slide, 5.4, 2.4, 2.5, t["accent"])

    _text(slide, "Thank You", 0, 2.7, W, 0.9, 52, RGBColor(255, 255, 255), True,
          PP_ALIGN.CENTER, font=t["serif"])

    _text(slide, trip_data.get("trip_name", ""),
          0, 3.75, W, 0.5, 20, t["accent_light"], False, PP_ALIGN.CENTER, font=t["sans"],
          italic=True)

    _thin_line(slide, 5.4, 4.5, 2.5, t["accent"])

    _text(slide, "Your journey begins here.", 0, 4.8, W, 0.5, 16,
          RGBColor(200, 200, 200), False, PP_ALIGN.CENTER, font=t["sans"])

    # Brand footer
    _text(slide, "VSL 360", 0, 6.5, W, 0.4, 12, t["accent"], True, PP_ALIGN.CENTER,
          font=t["sans"])


# ═══════════════════════════════════════════════════════════════════════════════
#  P U B L I C   A P I
# ═══════════════════════════════════════════════════════════════════════════════

def generate_vsl360_itinerary_slides(trip_data: Dict, output_path: Optional[str] = None) -> str:
    if not output_path:
        trip_name = trip_data.get("trip_name", "itinerary").replace(" ", "_").lower()
        out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "itineraries")
        output_path = os.path.join(out_dir, f"{trip_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pptx")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    trip_data = auto_populate_images(dict(trip_data))
    theme = _pick_theme(trip_data.get("template_name"))

    prs = Presentation()
    prs.slide_width = Inches(W)
    prs.slide_height = Inches(H)

    _add_cover_slide(prs, trip_data, theme)
    _add_overview_slide(prs, trip_data, theme)
    _add_route_slide(prs, trip_data, theme)

    for idx, day in enumerate(_safe_list(trip_data, "days")):
        _add_day_slide(prs, day, idx, theme)

    _add_hotels_slide(prs, trip_data, theme)
    _add_inclusions_slide(prs, trip_data, theme)
    _add_closing_slide(prs, trip_data, theme)

    prs.save(output_path)
    return output_path
