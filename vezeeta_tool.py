"""
vezeeta_tool.py
---------------
LangChain tool wrapping the Vezeeta doctor scraper.
بيحفظ النتائج في ملف JSON هيكله:
{
    "نفسي": {
        "مصر-الجديدة": [ {doctor}, {doctor}, ... ],
        "المعادي":      [ {doctor}, ... ]
    },
    "اسنان": {
        "الدقي-والمهندسين": [ {doctor}, ... ]
    }
}

الاستخدام:
    from Cairo_Care.vezeeta_tool import search_vezeeta_doctors

    # استدعاء مباشر
    result = search_vezeeta_doctors.invoke({
        "specialty": "نفسي",
        "area": "مصر-الجديدة",
        "top_n": 5,
    })
    # result -> list[dict]

    # ربط بأي LLM يدعم tool-calling
    llm_with_tools = llm.bind_tools([search_vezeeta_doctors])
"""

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
    """
    يدمج الدكاترة الجدد في الـ cache تحت specialty → area.
    - بيتجنب التكرار بناءً على profile_url
    - بيحتفظ بالترتيب (الأقدم أولاً)
    يرجع القائمة المدمجة النهائية.
    """
    existing: list[dict] = cache.get(specialty, {}).get(area, [])
    seen_urls: set[str] = {d.get("profile_url", "") for d in existing}
    unique_new = [d for d in new_doctors if d.get("profile_url", "") not in seen_urls]
    merged = existing + unique_new

    # حدّث الـ cache في الذاكرة
    if specialty not in cache:
        cache[specialty] = {}
    cache[specialty][area] = merged
    return merged


# ---------------------------------------------------------------------------
# LangChain @tool
# ---------------------------------------------------------------------------

@tool
def search_vezeeta_doctors(
    specialty: str,
    area: str,
    top_n: int = 5,
    include_sponsored: bool = False,
) -> list[dict]:
    """
    Search Vezeeta for the top-rated doctors by medical specialty and Cairo area.

    Use this tool whenever the user asks to find, recommend, or look up doctors,
    clinics, or specialists on Vezeeta in a specific area of Cairo.

    Results are persisted in a local JSON cache file (doctors_cache.json) structured
    as specialty → area → list of doctors, so repeated calls accumulate data.

    Returns a list of doctor dictionaries, each containing:
      - name:          Full doctor name (Arabic)
      - title:         Title prefix e.g. 'دكتور' / 'دكتورة' / 'خبير نفسي'
      - description:   Short bio / specialty description
      - fees:          Consultation fee in Arabic numerals (e.g. '٨٠٠')
      - rating:        Overall rating out of 5.0
      - ratings_count: Number of patient ratings
      - address:       Clinic address (area + street)
      - profile_url:   Full Vezeeta profile URL
      - sponsored:     Whether this is a paid/sponsored listing

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
    # 1. جيب النتائج من فيزيتا
    new_doctors = search_doctors(
        specialty=specialty,
        area=area,
        top_n=top_n,
        include_sponsored=include_sponsored,
    )

    # 2. حمّل الـ cache الحالي، ادمج، واحفظ
    cache = _load_cache()
    merged = _merge_into_cache(cache, specialty, area, new_doctors)
    _save_cache(cache)


    return new_doctors


