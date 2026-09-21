

import json
import sys
from pathlib import Path

from langchain_core.tools import tool

# إصلاح ترميز الحروف العربية على Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf-8-sig"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr.encoding and sys.stderr.encoding.lower() not in ("utf-8", "utf-8-sig"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# أضف مجلد Cairo_Care للـ path عشان الـ import يشتغل من أي مكان
_THIS_DIR = Path(__file__).parent
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))

from vzeeta import search_doctors  # noqa: E402

# ملف الـ cache المنظّم (specialty → area → doctors)
DOCTORS_CACHE_FILE = _THIS_DIR / "doctors_cache.json"


# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------

def _load_cache() -> dict:
    """يحمّل ملف الـ cache. يرجع dict فاضي لو الملف مش موجود أو تالف."""
    if not DOCTORS_CACHE_FILE.exists():
        return {}
    try:
        return json.loads(DOCTORS_CACHE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _save_cache(cache: dict) -> None:
    """يحفظ الـ cache في الملف."""
    DOCTORS_CACHE_FILE.write_text(
        json.dumps(cache, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _merge_into_cache(
    cache: dict,
    specialty: str,
    area: str,
    new_doctors: list[dict],
) -> list[dict]:

    existing: list[dict] = cache.get(specialty, {}).get(area, [])
    seen_urls: set[str] = {d.get("profile_url", "") for d in existing}
    unique_new = [d for d in new_doctors if d.get("profile_url", "") not in seen_urls]
    merged = existing + unique_new

    # حدّث الـ cache في الذاكرة
    if specialty not in cache:
        cache[specialty] = {}
    cache[specialty][area] = merged
    return merged



@tool
def search_vezeeta_doctors(
    specialty: str,
    area: str,
    top_n: int = 5,
    include_sponsored: bool = False,
) -> str:
    """
    Search Vezeeta for the top-rated doctors by medical specialty and Cairo area.

    Use this tool whenever the user asks to find, recommend, or look up doctors,
    clinics, or specialists on Vezeeta in a specific area of Cairo.

    Results are persisted in a local JSON cache file (doctors_cache.json) structured
    as specialty -> area -> list of doctors, so repeated calls accumulate data.

    Returns a formatted Arabic text block listing each doctor with:
      name, title, specialty description, fees, rating, address, profile URL.

    Args:
        specialty: Arabic specialty slug matching the Vezeeta URL format.
                   Examples: 'نفسي' (psychiatry), 'اسنان' (dentistry),
                   'عظام' (orthopedics), 'أطفال' (pediatrics), 'جلدية' (dermatology)
        area:      Arabic area slug matching the Vezeeta URL format.
                   Examples: 'مصر-الجديدة', 'الدقي-والمهندسين', 'المعادي',
                   'الزمالك', 'مدينة-نصر'
        top_n:     Maximum number of doctors to return, sorted by rating (default 5)
        include_sponsored: Whether to include paid/sponsored listings (default False)
    """
    # Normalize area slug
    try:
        from location_tools import match_cairo_district
        _, resolved_slug = match_cairo_district(area)
        if resolved_slug != "القاهرة" or area.strip() in ("القاهرة", "cairo"):
            area = resolved_slug
        else:
            area = area.strip().replace(" ", "-")
    except Exception:
        area = area.strip().replace(" ", "-")

    # 1. ابحث في الـ cache الأول — لو في نتائج مخزّنة ارجع بيها بدون scraping
    cache = _load_cache()
    cached = cache.get(specialty, {}).get(area, [])
    if cached:
        if not include_sponsored:
            cached = [d for d in cached if not d.get("sponsored", False)]
        return _format_doctors(cached[:top_n], specialty, area)

    # 2. الـ cache miss — اعمل scraping
    new_doctors = search_doctors(
        specialty=specialty,
        area=area,
        top_n=top_n,
        include_sponsored=include_sponsored,
    )

    # 3. ادمج في الـ cache واحفظ
    merged = _merge_into_cache(cache, specialty, area, new_doctors)
    _save_cache(cache)

    return _format_doctors(merged, specialty, area)


def _format_doctors(doctors: list, specialty: str, area: str) -> str:
    """Format a list of doctor dicts into a readable Arabic text block."""
    if not doctors:
        return f"لم يتم العثور على أطباء في تخصص '{specialty}' بمنطقة '{area}'."

    lines = [f"نتائج البحث عن دكتور {specialty} في {area}:\n"]
    for i, d in enumerate(doctors, 1):
        rating = d.get('rating', 'N/A')
        count  = d.get('ratings_count', 0)
        stars  = f"{rating}/5.0 ({count} تقييم)" if rating != 'N/A' else 'غير متوفر'
        lines.append(
            f"{i}. {d.get('title','')} {d.get('name','N/A')}\n"
            f"   التخصص: {d.get('description', 'N/A')}\n"
            f"   التقييم: {stars}\n"
            f"   الرسوم: {d.get('fees', 'غير محدد')} جنيه\n"
            f"   العنوان: {d.get('address', 'N/A')}\n"
            f"   الحجز: {d.get('profile_url', 'N/A')}"
        )
    return "\n\n".join(lines)
