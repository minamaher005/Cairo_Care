"""
Vezeeta Top Doctors Finder
---------------------------
يجيب أفضل الدكاترة حسب التخصص والمنطقة من صفحة نتائج البحث في فيزيتا،
بيرتبهم حسب التقييم وعدد الزوار، مع كاش بسيط وتحكم في معدل الطلبات
(Rate Limiting) عشان محدش يتحظر.

الاستخدام:
    python vezeeta_top_doctors.py نفسي مصر-الجديدة
    python vezeeta_top_doctors.py اسنان الدقي-والمهندسين --top 3

ملاحظة: الأسماء (specialty / area) لازم تكون بنفس صيغة الـ URL اللي فيزيتا
بتستخدمها (زي "نفسي" أو "مصر-الجديدة"). لو مش عارف الصيغة، افتح صفحة
البحث العادية في المتصفح وشوف الرابط.
"""

import argparse
import hashlib
import json
import os
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import requests

# إصلاح مشكلة ترميز الحروف العربية على Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf-8-sig"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr.encoding and sys.stderr.encoding.lower() not in ("utf-8", "utf-8-sig"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ---------------------------------------------------------------------------
# إعدادات عامة
# ---------------------------------------------------------------------------

BASE_URL = "https://www.vezeeta.com/ar/دكتور/{specialty}/{area}"
CACHE_DIR = Path(".vezeeta_cache")
CACHE_TTL_SECONDS = 60 * 30  # نصف ساعة - بعدها الكاش يعتبر قديم

# Rate limiting: أقل مدة مسموحة بين طلبين متتاليين للسيرفر (بالثواني)
MIN_REQUEST_INTERVAL = 3.0

# لو حصل 429 / حظر مؤقت، نعيد المحاولة بـ backoff تصاعدي
MAX_RETRIES = 4
BACKOFF_BASE_SECONDS = 5  # 5s, 10s, 20s, 40s...

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "ar-EG,ar;q=0.9,en;q=0.8",
}

# تحويل الأرقام العربية (الهندية) لأرقام إنجليزية
ARABIC_DIGITS = "٠١٢٣٤٥٦٧٨٩"
ENGLISH_DIGITS = "0123456789"
ARABIC_TO_ENGLISH_DIGITS = str.maketrans(ARABIC_DIGITS, ENGLISH_DIGITS)


def arabic_to_number(value) -> float:
    """يحول '١,٢٠٠' أو '٤.٥' أو None لرقم float قابل للمقارنة."""
    if value is None:
        return 0.0
    text = str(value).translate(ARABIC_TO_ENGLISH_DIGITS)
    text = text.replace(",", "").strip()
    try:
        return float(text)
    except ValueError:
        return 0.0


# ---------------------------------------------------------------------------
# محدد معدل الطلبات (Rate Limiter) بسيط قائم على ملف مشترك
# ---------------------------------------------------------------------------

class RateLimiter:
    """يضمن مسافة زمنية دنيا بين أي طلبين، حتى لو شغلت السكريبت أكتر من مرة."""

    def __init__(self, min_interval: float, lock_file: Path):
        self.min_interval = min_interval
        self.lock_file = lock_file

    def wait_if_needed(self):
        now = time.time()
        last = 0.0
        if self.lock_file.exists():
            try:
                last = float(self.lock_file.read_text().strip())
            except (ValueError, OSError):
                last = 0.0

        elapsed = now - last
        if elapsed < self.min_interval:
            sleep_for = self.min_interval - elapsed
            print(f"⏳ استنى {sleep_for:.1f} ثانية عشان معدل الطلبات...", file=sys.stderr)
            time.sleep(sleep_for)

        self.lock_file.parent.mkdir(parents=True, exist_ok=True)
        self.lock_file.write_text(str(time.time()))


# ---------------------------------------------------------------------------
# نموذج بيانات الدكتور
# ---------------------------------------------------------------------------

@dataclass
class Doctor:
    name: str
    title: str = ""
    description: str = ""
    specialty: str = ""
    sub_specialties: list = field(default_factory=list)
    fees: str = ""
    fees_value: float = 0.0
    rating_percentage: float = 0.0
    ratings_count: int = 0
    address: str = ""
    area: str = ""
    profile_url: str = ""
    image_url: str = ""
    is_sponsored: bool = False
    waiting_time_minutes: Optional[float] = None

    def score(self) -> tuple:
        """معيار الترتيب: التقييم الأعلى، وعند التساوي عدد الزوار الأكبر."""
        return (self.rating_percentage, self.ratings_count)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "title": self.title,
            "description": self.description,
            "fees": self.fees,
            "rating": self.rating_percentage,
            "ratings_count": self.ratings_count,
            "address": f"{self.area}: {self.address}".strip(": "),
            "profile_url": self.profile_url,
            "sponsored": self.is_sponsored,
        }


# ---------------------------------------------------------------------------
# جلب وتحليل الصفحة
# ---------------------------------------------------------------------------

def cache_path_for(url: str) -> Path:
    key = hashlib.sha256(url.encode("utf-8")).hexdigest()
    return CACHE_DIR / f"{key}.json"


def load_from_cache(url: str) -> Optional[str]:
    path = cache_path_for(url)
    if not path.exists():
        return None
    age = time.time() - path.stat().st_mtime
    if age > CACHE_TTL_SECONDS:
        return None
    return path.read_text(encoding="utf-8")


def save_to_cache(url: str, html: str):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path_for(url).write_text(html, encoding="utf-8")


def fetch_html(url: str, rate_limiter: RateLimiter) -> str:
    """يجيب الـ HTML مع كاش + rate limiting + إعادة محاولة عند 429/حظر."""
    cached = load_from_cache(url)
    if cached is not None:
        print("✅ استخدمنا نسخة مخزنة (cache) بدل ما نطلب من فيزيتا تاني.", file=sys.stderr)
        return cached

    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        rate_limiter.wait_if_needed()
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
        except requests.RequestException as e:
            last_error = e
            wait = BACKOFF_BASE_SECONDS * (2 ** (attempt - 1))
            print(f"⚠️ خطأ في الاتصال ({e}). محاولة {attempt}/{MAX_RETRIES}، هستنى {wait}s", file=sys.stderr)
            time.sleep(wait)
            continue

        if resp.status_code == 200:
            save_to_cache(url, resp.text)
            return resp.text

        if resp.status_code == 429 or resp.status_code >= 500:
            wait = BACKOFF_BASE_SECONDS * (2 ** (attempt - 1))
            retry_after = resp.headers.get("Retry-After")
            if retry_after:
                try:
                    wait = max(wait, float(retry_after))
                except ValueError:
                    pass
            print(
                f"🚫 السيرفر رجّع {resp.status_code} (ممكن يكون rate limit). "
                f"محاولة {attempt}/{MAX_RETRIES}، هستنى {wait:.0f} ثانية...",
                file=sys.stderr,
            )
            time.sleep(wait)
            continue

        # حالات تانية (404 مثلاً) مفيش داعي نعيد المحاولة
        resp.raise_for_status()

    raise RuntimeError(f"فشلنا بعد {MAX_RETRIES} محاولات. آخر خطأ: {last_error}")


def extract_next_data(html: str) -> dict:
    match = re.search(
        r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>',
        html,
        re.DOTALL,
    )
    if not match:
        raise ValueError("مقدرناش نلاقي بيانات __NEXT_DATA__ في الصفحة، ممكن الموقع غيّر شكله.")
    return json.loads(match.group(1))


def parse_doctors(next_data: dict, debug: bool = False) -> list:
    props = next_data.get("props", {})

    if debug:
        print("\n[DEBUG] __NEXT_DATA__ keys:", list(next_data.keys()), file=sys.stderr)
        print("[DEBUG] props keys:", list(props.keys()), file=sys.stderr)
        initial_state_dbg = props.get("initialState", {})
        print("[DEBUG] initialState keys:", list(initial_state_dbg.keys()), file=sys.stderr)
        common_dbg = initial_state_dbg.get("common", {})
        print("[DEBUG] initialState.common keys:", list(common_dbg.keys()), file=sys.stderr)
        sdr_dbg = common_dbg.get("searchDoctorsResults", {})
        print("[DEBUG] common.searchDoctorsResults keys:", list(sdr_dbg.keys()) if isinstance(sdr_dbg, dict) else type(sdr_dbg), file=sys.stderr)
        result_dbg = sdr_dbg.get("Result", []) if isinstance(sdr_dbg, dict) else []
        print(f"[DEBUG] Result count (common path): {len(result_dbg)}", file=sys.stderr)
        print("[DEBUG] Full JSON (first 4000 chars):", json.dumps(next_data, ensure_ascii=False)[:4000], file=sys.stderr)

    # --- Try all known paths in order ---
    initial_state = (
        props.get("initialState")
        or props.get("pageProps", {}).get("initialState")
    )
    if not initial_state:
        raise ValueError(
            "لا يوجد initialState في الـ props. "
            "جرب تشغل السكريبت بـ --debug عشان تشوف البيانات الكاملة."
        )

    results = []

    # Path 1 (Vezeeta 2024+): props.initialState.common.searchDoctorsResults.Result
    common = initial_state.get("common", {})
    common_dr = common.get("searchDoctorsResults", {})
    if isinstance(common_dr, dict):
        results = common_dr.get("Result", [])

    # Path 2 (old): props.initialState.search.searchDoctorsResults.Result
    if not results:
        search_state = initial_state.get("search", {})
        search_dr = search_state.get("searchDoctorsResults") or {}
        if isinstance(search_dr, dict):
            results = search_dr.get("Result", [])

    # Path 3: props.pageProps.initialState.search.searchDoctorsResults.Result
    if not results:
        page_props_state = props.get("pageProps", {}).get("initialState", {})
        old_search = page_props_state.get("search", {}).get("searchDoctorsResults") or {}
        if isinstance(old_search, dict):
            results = old_search.get("Result", [])

    # Fallback: sponsored ads (مدفوعة)
    if not results:
        search_state = initial_state.get("search", {})
        sponsored_raw = search_state.get("searchSponsoredAdsResults", [])
        results = [
            entry["data"] for entry in sponsored_raw
            if isinstance(entry.get("data"), dict) and entry["data"].get("DoctorName")
        ]
        if results:
            print("⚠️  النتائج مدفوعة (إعلانات) فقط - لم تُعثر على نتائج عادية.", file=sys.stderr)


    doctors = []
    for item in results:
        rating_model = item.get("DoctorRatingViewModel") or {}
        waiting = rating_model.get("WaitingTimeTotalMinutesOverallRating")

        doc = Doctor(
            name=item.get("DoctorName", "").strip(),
            title=item.get("PrefixTitle", ""),
            description=item.get("ShortDescription", ""),
            specialty=item.get("MainSpecialtyName", ""),
            sub_specialties=[s.get("Name") for s in item.get("SecondarySpecialties", [])],
            fees=item.get("Fees", ""),
            fees_value=arabic_to_number(item.get("Fees")),
            rating_percentage=arabic_to_number(item.get("OverallPercentage")),
            ratings_count=int(arabic_to_number(item.get("RatingsCount"))),
            address=item.get("BasicContactAddress", ""),
            area=(item.get("BasicContactArea") or {}).get("text", ""),
            profile_url="https://www.vezeeta.com/ar/dr/" + item.get("UrlName", ""),
            image_url=item.get("ImageUrl", ""),
            is_sponsored=bool(item.get("IsSponsored", False)),
            waiting_time_minutes=waiting,
        )
        if doc.name:
            doctors.append(doc)
    return doctors


def get_top_doctors(
    specialty: str,
    area: str,
    top_n: int = 5,
    include_sponsored: bool = False,
    rate_limiter: Optional[RateLimiter] = None,
    debug: bool = False,
) -> list:
    rate_limiter = rate_limiter or RateLimiter(MIN_REQUEST_INTERVAL, CACHE_DIR / ".last_request")
    url = BASE_URL.format(specialty=specialty, area=area)
    print(f"🌐 جاري الاتصال بـ: {url}", file=sys.stderr)

    html = fetch_html(url, rate_limiter)
    next_data = extract_next_data(html)
    doctors = parse_doctors(next_data, debug=debug)

    if not include_sponsored:
        doctors = [d for d in doctors if not d.is_sponsored]

    doctors.sort(key=lambda d: d.score(), reverse=True)
    return doctors[:top_n]


def search_doctors(
    specialty: str,
    area: str,
    top_n: int = 5,
    include_sponsored: bool = False,
) -> list[dict]:
    """
    واجهة برمجية نظيفة (Public API) للاستخدام كـ LangChain tool أو أي مكان تاني.

    بترجع list[dict] بدل list[Doctor] عشان التسلسل (serialization) يكون سهل.
    كل dict فيها: name, title, description, fees, rating, ratings_count,
                  address, profile_url, sponsored.

    Args:
        specialty: اسم التخصص زي هيظهر في رابط فيزيتا (مثال: 'نفسي', 'اسنان')
        area:      اسم المنطقة زي هيظهر في رابط فيزيتا (مثال: 'مصر-الجديدة', 'الدقي-والمهندسين')
        top_n:     عدد الدكاترة المطلوب (افتراضي 5)
        include_sponsored: هل تشمل الإعلانات الممولة؟ (افتراضي False)
    """
    doctors = get_top_doctors(
        specialty=specialty,
        area=area,
        top_n=top_n,
        include_sponsored=include_sponsored,
    )
    return [doc.to_dict() for doc in doctors]


# ---------------------------------------------------------------------------
# واجهة سطر الأوامر
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="جيب أفضل الدكاترة من فيزيتا حسب التخصص والمنطقة.")
    parser.add_argument("specialty", help="اسم التخصص زي هيظهر في رابط فيزيتا، مثال: نفسي")
    parser.add_argument("area", help="اسم المنطقة زي هيظهر في رابط فيزيتا، مثال: مصر-الجديدة")
    parser.add_argument("--top", type=int, default=5, help="عدد الدكاترة المطلوب إرجاعهم (افتراضي 5)")
    parser.add_argument("--include-sponsored", action="store_true", help="اشمل الإعلانات الممولة في الترتيب")
    parser.add_argument("--json", action="store_true", help="اطبع النتيجة بصيغة JSON في التيرمينال")
    parser.add_argument("--output", metavar="FILE", default=None,
                        help="احفظ النتيجة في ملف JSON (لو مش محدد اسم، هيتعمل تلقائي زي: نفسي_مصر-الجديدة.json)")
    parser.add_argument("--debug", action="store_true", help="اطبع بيانات __NEXT_DATA__ الخام عشان تشخّص مشاكل البنية")
    parser.add_argument("--no-cache", action="store_true", help="تجاهل الكاش وأجيب البيانات من فيزيتا مباشرةً")
    args = parser.parse_args()

    # امسح الكاش لو المستخدم طلب
    if args.no_cache:
        import shutil
        if CACHE_DIR.exists():
            shutil.rmtree(CACHE_DIR)
            print("🗑️ تم مسح الكاش.", file=sys.stderr)

    try:
        top_doctors = get_top_doctors(
            specialty=args.specialty,
            area=args.area,
            top_n=args.top,
            include_sponsored=args.include_sponsored,
            debug=args.debug,
        )
    except Exception as e:
        print(f"❌ حصل خطأ: {e}", file=sys.stderr)
        sys.exit(1)

    if not top_doctors:
        print("مفيش نتائج، تأكد من صيغة التخصص والمنطقة.")
        return

    data_out = [d.to_dict() for d in top_doctors]

    # --- حفظ في ملف JSON ---
    # الاسم التلقائي: نفس مجلد السكريبت / specialty_area.json
    script_dir = Path(__file__).parent
    auto_name = script_dir / f"{args.specialty}_{args.area}.json"

    if args.output is not None:
        out_file = Path(args.output)
    else:
        out_file = auto_name

    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(
        json.dumps(data_out, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"💾 تم الحفظ في: {out_file.resolve()}", file=sys.stderr)

    # --- طباعة في التيرمينال ---
    if args.json:
        print(json.dumps(data_out, ensure_ascii=False, indent=2))
        return

    print(f"\n🏆 أفضل {len(top_doctors)} دكتور - {args.specialty} في {args.area}\n" + "=" * 50)
    for i, doc in enumerate(top_doctors, start=1):
        stars = "⭐" * round(doc.rating_percentage)
        print(f"\n{i}. {doc.title} {doc.name}".strip())
        if doc.description:
            print(f"   {doc.description}")
        print(f"   {stars} ({doc.rating_percentage}/5) من {doc.ratings_count} تقييم")
        if doc.fees:
            print(f"   💰 الكشف: {doc.fees} جنيه")
        if doc.area or doc.address:
            print(f"   📍 {doc.area}: {doc.address}")
        print(f"   🔗 {doc.profile_url}")


if __name__ == "__main__":
    main()