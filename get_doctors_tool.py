

import json
import sys
from pathlib import Path

from langchain_core.tools import tool

# ------------------- path setup -------------------
_THIS_DIR = Path(__file__).parent
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))

# إصلاح ترميز Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf-8-sig"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr.encoding and sys.stderr.encoding.lower() not in ("utf-8", "utf-8-sig"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from vezeeta_tool import search_vezeeta_doctors  # noqa: E402

DOCTORS_CACHE_FILE = _THIS_DIR / "doctors_cache.json"



def _read_cache(specialty: str, area: str) -> list[dict] | None:

    if not DOCTORS_CACHE_FILE.exists():
        return None
    try:
        cache = json.loads(DOCTORS_CACHE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None

    return cache.get(specialty, {}).get(area) or None



@tool
def get_doctors(specialty: str, area: str, top_n: int = 5) -> dict:
    """
    Find top-rated doctors for a given medical specialty and Cairo area.

    Use this tool when the patient's symptoms are NOT urgent and they need
    to book a clinic appointment. This is the PREFERRED tool for doctor lookup
    because it checks the local cache first before making any network request.

    Decision logic (internal, transparent to the agent):
      - If doctors for this specialty + area exist in the local cache → returns
        them instantly without hitting Vezeeta (source = 'cache').
      - If not found in cache → scrapes Vezeeta, saves to cache, then returns
        fresh results (source = 'vezeeta').

    Args:
        specialty: Arabic specialty slug as it appears in the Vezeeta URL.
                   Map patient symptoms to the closest specialty:
                   - Anxiety / Depression / Psychiatric issues  → 'نفسي'
                   - Toothache / Cavities / Dental problems    → 'اسنان'
                   - Fractures / Joint pain / Orthopedics      → 'عظام'
                   - Fever / Common cold / Pediatrics          → 'أطفال'
                   - Skin rash / Allergies / Dermatology       → 'جلدية'
                   - Heart issues / Hypertension / Cardiology  → 'قلب'
                   - Diabetes / Hormonal disorders             → 'غدد-صماء'
        area:     Arabic area slug as it appears in the Vezeeta URL.
                  Examples:
                  - 'مصر-الجديدة' (Heliopolis)
                  - 'المعادي' (Maadi)
                  - 'الدقي-والمهندسين' (Dokki & Mohandessin)
                  - 'مدينة-نصر' (Nasr City)
                  - 'الزمالك' (Zamalek)
                  - 'شبرا' (Shubra)
                  - 'العباسية' (Abbassia)
        top_n:    Maximum doctors to return (default 5).

    Returns a dict with two keys:
        {
            "source":  "cache" | "vezeeta",
            "doctors": [
                {
                    "name":          str,   # Doctor's full name
                    "title":         str,   # Title (e.g., Doctor / Specialist / Consultant)
                    "description":   str,   # Short bio / sub-specialty details
                    "fees":          str,   # Consultation fees
                    "rating":        float, # Rating score out of 5
                    "ratings_count": int,   # Total number of reviews
                    "address":       str,   # Area and street address
                    "profile_url":   str,   # Vezeeta doctor profile link
                    "sponsored":     bool   # Whether the listing is sponsored/promoted
                },
                ...
            ]
        }
    """

    # ---- 1. Check cache ----
    cached = _read_cache(specialty, area)

    if cached is not None:
       
        result = cached[:top_n]

        return result


    fresh = search_vezeeta_doctors.invoke(
        {"specialty": specialty, "area": area, "top_n": top_n}
    )
 

    return fresh
