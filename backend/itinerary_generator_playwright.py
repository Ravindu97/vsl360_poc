from datetime import datetime
import base64
import json
import mimetypes
import os
from typing import Any, Dict, Optional, Tuple

import requests
from image_generator import auto_populate_images


LOCAL_IMAGE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sample_itinerary", "images")
)
TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
DEFAULT_TEMPLATE_ID = "elegant_classic"


def _resolve_image_source_to_local(source: str) -> Tuple[Optional[str], bool]:
    """
    Resolve an image source into a local file path.
    Returns (path, is_temp) where is_temp means caller should delete it.
    """
    if not source:
        return None, False

    normalized = source.strip()
    if normalized.startswith("http://") or normalized.startswith("https://"):
        return None, False

    candidates = []
    if os.path.isabs(normalized):
        candidates.append(normalized)
    else:
        candidates.append(os.path.join(LOCAL_IMAGE_DIR, normalized))
        candidates.append(os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", normalized)))
        candidates.append(os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), normalized)))

    for candidate in candidates:
        if os.path.isfile(candidate):
            return candidate, False

    return None, False


def _bytes_to_data_uri(data: bytes, source_name: str) -> str:
    mime, _ = mimetypes.guess_type(source_name)
    if not mime:
        mime = "image/jpeg"
    encoded = base64.b64encode(data).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def _image_source_to_data_uri(source: Optional[str]) -> Optional[str]:
    if not source:
        return None

    try:
        if source.startswith("http://") or source.startswith("https://"):
            response = requests.get(source, timeout=20)
            response.raise_for_status()
            return _bytes_to_data_uri(response.content, source)

        local_path, _ = _resolve_image_source_to_local(source)
        if local_path:
            with open(local_path, "rb") as f:
                return _bytes_to_data_uri(f.read(), local_path)
    except Exception:
        return None

    return None


def _safe_template_id(template_id: Optional[str]) -> str:
    if not template_id:
        return DEFAULT_TEMPLATE_ID
    # Keep template loading path-safe.
    return "".join(ch for ch in template_id if ch.isalnum() or ch in {"_", "-"}) or DEFAULT_TEMPLATE_ID


def _load_template_pack(template_id: Optional[str]) -> Dict[str, Any]:
    resolved_template_id = _safe_template_id(template_id)
    template_dir = os.path.join(TEMPLATES_DIR, resolved_template_id)
    if not os.path.isdir(template_dir):
        template_dir = os.path.join(TEMPLATES_DIR, DEFAULT_TEMPLATE_ID)
        resolved_template_id = DEFAULT_TEMPLATE_ID

    template_html_path = os.path.join(template_dir, "template.html")
    styles_css_path = os.path.join(template_dir, "styles.css")
    preset_json_path = os.path.join(template_dir, "preset.json")

    if not os.path.exists(template_html_path) or not os.path.exists(styles_css_path):
        raise RuntimeError(f"Template pack is incomplete: {template_dir}")

    with open(styles_css_path, "r", encoding="utf-8") as f:
        css_text = f.read()

    preset = {
        "id": resolved_template_id,
        "label": resolved_template_id,
        "description": "",
        "tokens": {},
        "layout": {},
    }
    if os.path.exists(preset_json_path):
        with open(preset_json_path, "r", encoding="utf-8") as f:
            loaded = json.load(f)
            if isinstance(loaded, dict):
                preset.update(loaded)

    return {
        "id": resolved_template_id,
        "template_dir": template_dir,
        "template_file": os.path.basename(template_html_path),
        "css_text": css_text,
        "preset": preset,
    }


def _build_css_variables(pack: Dict[str, Any]) -> str:
    preset = pack.get("preset", {})
    tokens = dict(preset.get("tokens", {}) or {})
    layout = dict(preset.get("layout", {}) or {})

    css_vars = []
    for key, value in tokens.items():
        css_vars.append(f"--{str(key).replace('_', '-')}: {value};")

    mm_keys = {"page_padding_mm", "cover_image_height_mm", "day_image_height_mm", "day_image_width_mm"}
    px_keys = {"corner_radius_px", "title_tracking_px"}

    for key, value in layout.items():
        css_key = str(key).replace("_", "-")
        if key in mm_keys:
            css_vars.append(f"--{css_key}: {value}mm;")
        elif key in px_keys:
            css_vars.append(f"--{css_key}: {value}px;")
        else:
            css_vars.append(f"--{css_key}: {value};")

    return "\n            ".join(css_vars)


def list_template_presets() -> Dict[str, Any]:
    templates = []
    if not os.path.isdir(TEMPLATES_DIR):
        return {"default": DEFAULT_TEMPLATE_ID, "templates": templates}

    for name in sorted(os.listdir(TEMPLATES_DIR)):
        directory = os.path.join(TEMPLATES_DIR, name)
        if not os.path.isdir(directory):
            continue
        preset_file = os.path.join(directory, "preset.json")
        if os.path.exists(preset_file):
            with open(preset_file, "r", encoding="utf-8") as f:
                preset = json.load(f)
        else:
            preset = {"id": name, "label": name, "description": "", "tokens": {}, "layout": {}}
        templates.append(preset)

    return {"default": DEFAULT_TEMPLATE_ID, "templates": templates}


def _build_template_data(trip_data: Dict) -> Dict:
    # Auto-populate missing images from Unsplash or placeholders
    trip_data = auto_populate_images(trip_data)
    days = trip_data.get("days", []) or []
    template_days = []
    for day in days:
        day_copy = dict(day)
        day_image_source = day_copy.get("image_path") or day_copy.get("image_url")
        day_copy["image_data_uri"] = _image_source_to_data_uri(day_image_source)
        template_days.append(day_copy)

    cover_source = trip_data.get("cover_image_path") or trip_data.get("cover_image_url")
    template_name = trip_data.get("template_name")
    pack = _load_template_pack(template_name)

    return {
        "customer_name": trip_data.get("customer_name", ""),
        "trip_name": trip_data.get("trip_name", "Travel Itinerary"),
        "destination_country": trip_data.get("destination_country", ""),
        "total_days": trip_data.get("total_days", 0),
        "total_nights": trip_data.get("total_nights", 0),
        "start_date": trip_data.get("start_date", ""),
        "end_date": trip_data.get("end_date", ""),
        "overview_text": trip_data.get("overview_text", ""),
        "location_summary": trip_data.get("location_summary", []) or [],
        "days": template_days,
        "hotels": trip_data.get("hotels", []) or [],
        "tour_includes": trip_data.get("tour_includes", []) or [],
        "tour_excludes": trip_data.get("tour_excludes", []) or [],
        "cost_per_person": trip_data.get("cost_per_person", ""),
        "payment_info": trip_data.get("payment_info", []) or [],
        "cancellation_policy": trip_data.get("cancellation_policy", []) or [],
        "cover_image_data_uri": _image_source_to_data_uri(cover_source),
        "generation_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "template_id": pack.get("id"),
        "css_text": pack.get("css_text", ""),
        "css_variables": _build_css_variables(pack),
        "template_dir": pack.get("template_dir"),
        "template_file": pack.get("template_file"),
    }


def generate_vsl360_itinerary_pdf_playwright(trip_data: Dict, output_path: Optional[str] = None) -> str:
    """
    Generate VSL-style itinerary PDF using HTML/CSS rendered by Chromium.
    """
    if not output_path:
        trip_name = trip_data.get("trip_name", "itinerary").replace(" ", "_").lower()
        itineraries_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "itineraries")
        output_path = os.path.join(itineraries_dir, f"{trip_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_v2.pdf")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    rendered_data = _build_template_data(trip_data)

    try:
        from jinja2 import Environment, FileSystemLoader, select_autoescape
    except ImportError as exc:
        raise RuntimeError("jinja2 is not installed. Run: pip install -r requirements.txt") from exc

    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError("playwright is not installed. Run: pip install -r requirements.txt") from exc

    env = Environment(
        loader=FileSystemLoader(rendered_data["template_dir"]),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template(rendered_data["template_file"])

    html = template.render(**rendered_data)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1240, "height": 1754})
            page.set_content(html, wait_until="networkidle")
            page.pdf(
                path=output_path,
                format="A4",
                print_background=True,
                margin={"top": "0mm", "right": "0mm", "bottom": "0mm", "left": "0mm"},
            )
            browser.close()
    except Exception as exc:
        raise RuntimeError(
            "Playwright PDF generation failed. Ensure Chromium is installed with: playwright install chromium"
        ) from exc

    return output_path
