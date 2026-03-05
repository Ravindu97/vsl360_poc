from datetime import datetime
import base64
import mimetypes
import os
from typing import Dict, Optional, Tuple

import requests


LOCAL_IMAGE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sample_itinerary", "images")
)


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


def _build_template_data(trip_data: Dict) -> Dict:
    days = trip_data.get("days", []) or []
    template_days = []
    for day in days:
        day_copy = dict(day)
        day_image_source = day_copy.get("image_path") or day_copy.get("image_url")
        day_copy["image_data_uri"] = _image_source_to_data_uri(day_image_source)
        template_days.append(day_copy)

    cover_source = trip_data.get("cover_image_path") or trip_data.get("cover_image_url")

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

    template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "itinerary_template_v2.html")

    try:
        from jinja2 import Environment, FileSystemLoader, select_autoescape
    except ImportError as exc:
        raise RuntimeError("jinja2 is not installed. Run: pip install -r requirements.txt") from exc

    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError("playwright is not installed. Run: pip install -r requirements.txt") from exc

    env = Environment(
        loader=FileSystemLoader(os.path.dirname(template_path)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template(os.path.basename(template_path))

    html = template.render(**_build_template_data(trip_data))

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
