import math

import requests
from langchain.tools import tool

try:
    from src.backend.config import LOCATIONIQ_API_KEY, QDRANT_COLLECTION
    from src.backend.rag.vector_store import get_qdrant_client
except ImportError:
    try:
        from config import LOCATIONIQ_API_KEY, QDRANT_COLLECTION
        from vector_store import get_qdrant_client
    except ImportError:
        LOCATIONIQ_API_KEY = "pk.4d2409895ce6cf67da0d278af713b4d3"
        QDRANT_COLLECTION = "hospitals"
        def get_qdrant_client():
            from qdrant_client import QdrantClient
            return QdrantClient(url="http://localhost:6333")


LOCATIONIQ_BASE = "https://us1.locationiq.com/v1"


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return the straight-line distance between two points in kilometers."""
    earth_radius_km = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    value = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    return earth_radius_km * 2 * math.atan2(math.sqrt(value), math.sqrt(1 - value))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Cairo District & Vezeeta Area Mapping
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CAIRO_DISTRICT_PATTERNS = [
    (("معادي", "maadi"), "المعادي", "المعادي"),
    (("نصر", "nasr"), "مدينة نصر", "مدينة-نصر"),
    (("مصر الجديدة", "هليوبوليس", "heliopolis", "نزهة", "شيراتون"), "مصر الجديدة", "مصر-الجديدة"),
    (("دقى", "دقي", "مهندسين", "dokki", "mohandessin", "عجوزة"), "الدقي والمهندسين", "الدقي-والمهندسين"),
    (("زمالك", "zamalek"), "الزمالك", "الزمالك"),
    (("تجمع", "القاهرة الجديدة", "tagamoa", "new cairo", "رحاب", "مدينتي"), "التجمع الخامس", "التجمع"),
    (("شبرا", "shoubra", "shubra", "ساحل", "روض الفرج"), "شبرا", "شبرا"),
    (("وسط البلد", "التحرير", "downtown", "tahrir", "عابدين", "قصر العيني", "عتبه", "عتبة", "باب الشعرية", "ازهر", "أزهر", "سيدة زينب", "العشماوى", "جمالية"), "وسط البلد", "وسط-البلد"),
    (("هرم", "فيصل", "haram", "faisal", "جيزة", "giza"), "الهرم والجيزة", "الهرم"),
    (("مقطم", "mokattam"), "المقطم", "المقطم"),
    (("شيخ زايد", "زايد", "zayed"), "الشيخ زايد", "الشيخ-زايد"),
    (("اكتوبر", "أكتوبر", "october"), "6 أكتوبر", "6-اكتوبر"),
    (("عين شمس", "ain shams", "مطرية"), "عين شمس", "عين-شمس"),
    (("زيتون", "zaytoun", "أميرية", "اميرية"), "الزيتون", "الزيتون"),
    (("حلوان", "helwan", "المعصرة"), "حلوان", "حلوان"),
    (("عباسية", "وايلي"), "العباسية", "الوايلي-والعباسية"),
]

def match_cairo_district(text: str) -> tuple[str, str]:
    """Matches any free text / address string to (Display Arabic Name, Vezeeta Slug)."""
    if not text:
        return ("القاهرة", "القاهرة")
    t = text.lower()
    for kw_list, display_name, slug in CAIRO_DISTRICT_PATTERNS:
        if any(k in t for k in kw_list):
            return (display_name, slug)
    return ("القاهرة", "القاهرة")


def reverse_geocode(lat: float, lon: float) -> dict:
    """
    Reverse geocodes latitude and longitude into display name,
    Cairo district, and matching Vezeeta area slug.
    """
    try:
        params = {
            "key": LOCATIONIQ_API_KEY,
            "lat": lat,
            "lon": lon,
            "format": "json",
            "accept-language": "ar",
        }
        response = requests.get(f"{LOCATIONIQ_BASE}/reverse.php", params=params, timeout=10)
        if response.status_code != 200:
            return {
                "lat": lat,
                "lon": lon,
                "display_name": f"{lat}, {lon}",
                "district": "القاهرة",
                "area_slug": "القاهرة",
                "error": response.text,
            }
        data = response.json()
        display_name = data.get("display_name", "")
        addr = data.get("address", {})
        
        # Combine address fields for matching
        combined_text = " ".join([
            addr.get("neighbourhood", ""),
            addr.get("suburb", ""),
            addr.get("quarter", ""),
            addr.get("city_district", ""),
            addr.get("city", ""),
            display_name,
        ])
        
        district, area_slug = match_cairo_district(combined_text)
        
        return {
            "lat": lat,
            "lon": lon,
            "display_name": display_name,
            "district": district,
            "area_slug": area_slug,
            "address": addr,
        }
    except Exception as e:
        return {
            "lat": lat,
            "lon": lon,
            "display_name": f"{lat}, {lon}",
            "district": "القاهرة",
            "area_slug": "القاهرة",
            "error": str(e),
        }


def get_ip_location() -> dict:
    """
    Detects the user's approximate location based on public IP address
    and resolves it to a Cairo district and Vezeeta area.
    """
    try:
        r = requests.get("http://ip-api.com/json", timeout=4)
        if r.status_code == 200:
            d = r.json()
            if d.get("status") == "success":
                lat = float(d.get("lat", 30.0444))
                lon = float(d.get("lon", 31.2357))
                res = reverse_geocode(lat, lon)
                res["source"] = "تلقائي (IP)"
                return res
    except Exception:
        pass
    return {
        "lat": 30.0444,
        "lon": 31.2357,
        "display_name": "وسط البلد، القاهرة",
        "district": "وسط البلد",
        "area_slug": "وسط-البلد",
        "source": "افتراضي",
    }


@tool
def get_user_coordinates(location_name: str) -> str:
    """Convert a Cairo location name into latitude and longitude."""
    if not LOCATIONIQ_API_KEY:
        return "⚠️ مفتاح LocationIQ غير مضبوط في ملف البيئة."

    try:
        response = requests.get(
            f"{LOCATIONIQ_BASE}/search.php",
            params={
                "key": LOCATIONIQ_API_KEY,
                "q": f"{location_name}, Cairo, Egypt",
                "format": "json",
                "limit": 1,
            },
            timeout=10,
        )
        if response.status_code != 200:
            return f"⚠️ خطأ في تحديد الموقع: {response.text}"

        data = response.json()
        if not data:
            return f"⚠️ لم أتمكن من العثور على موقع: {location_name}"

        result = data[0]
        lat = float(result["lat"])
        lon = float(result["lon"])
        display_name = result.get("display_name", location_name)
        district, slug = match_cairo_district(display_name + " " + location_name)
        return (
            f"location: {display_name}\n"
            f"latitude: {lat}\n"
            f"longitude: {lon}\n"
            f"district: {district}\n"
            f"vezeeta_area: {slug}"
        )
    except (KeyError, TypeError, ValueError) as exc:
        return f"⚠️ بيانات الموقع غير صالحة: {exc}"
    except requests.RequestException as exc:
        return f"⚠️ تعذر الاتصال بخدمة تحديد الموقع: {exc}"


@tool
def reverse_geocode_location(lat: float, lon: float) -> str:
    """
    Converts GPS coordinates (latitude and longitude) into the user's
    Cairo neighborhood, district, and readable address using LocationIQ.
    Use this when you have user coordinates and need to identify their area or district.
    """
    res = reverse_geocode(lat, lon)
    if "error" in res and res.get("error"):
        return f"الإحداثيات: {lat}, {lon} (تعذر استرداد العنوان التفصيلي)"
    return (
        f"📍 العنوان: {res['display_name']}\n"
        f"🏙️ الحي/المنطقة: {res['district']}\n"
        f"🔗 منطقة فيزيتا: {res['area_slug']}\n"
        f"📌 الإحداثيات: {lat}, {lon}"
    )


@tool
def find_nearest_hospitals(user_lat: float, user_lon: float, specialty: str = "") -> str:
    """Return the three closest hospitals to coordinates from the local database."""
    try:
        client = get_qdrant_client()
        records, _ = client.scroll(
            collection_name=QDRANT_COLLECTION,
            limit=10000,
            with_payload=True,
            with_vectors=False,
        )
        metadata_rows = [
            record.payload.get("metadata", record.payload) 
            for record in records if record.payload
        ]
    except Exception as exc:
        return f"⚠️ تعذر قراءة قاعدة بيانات المستشفيات: {exc}"

    hospitals = []
    for metadata in metadata_rows:
        try:
            latitude = float(metadata["lat"])
            longitude = float(metadata["lon"])
        except (KeyError, TypeError, ValueError):
            continue

        if specialty and specialty.casefold() not in str(metadata.get("specialty", "")).casefold():
            continue

        hospitals.append(
            {
                "name": metadata.get("name", "N/A"),
                "address": metadata.get("address", "N/A"),
                "specialty": metadata.get("specialty", "N/A"),
                "phone": metadata.get("phone", "N/A"),
                "distance_km": round(haversine_distance(user_lat, user_lon, latitude, longitude), 2),
                "lat": latitude,
                "lon": longitude,
            }
        )

    if not hospitals and specialty:
        return find_nearest_hospitals.invoke({"user_lat": user_lat, "user_lon": user_lon})

    hospitals.sort(key=lambda hospital: hospital["distance_km"])
    nearest = hospitals[:3]
    if not nearest:
        return "لم يتم العثور على مستشفيات في قاعدة البيانات."

    return "✅ أقرب المستشفيات لموقعك:\n\n" + "\n\n".join(
        f"{index}. **{hospital['name']}**\n"
        f"   📏 المسافة: {hospital['distance_km']} كم\n"
        f"   📍 العنوان: {hospital['address']}\n"
        f"   🏥 التخصص: {hospital['specialty']}\n"
        f"   📞 الهاتف: {hospital['phone']}"
        for index, hospital in enumerate(nearest, 1)
    )


@tool
def get_driving_route(
    origin_lat: float,
    origin_lon: float,
    dest_lat: float,
    dest_lon: float,
) -> str:
    """Return driving distance and estimated travel time using LocationIQ."""
    if not LOCATIONIQ_API_KEY:
        return "⚠️ مفتاح LocationIQ غير مضبوط في ملف البيئة."

    try:
        response = requests.get(
            f"{LOCATIONIQ_BASE}/directions/driving/"
            f"{origin_lon},{origin_lat};{dest_lon},{dest_lat}",
            params={
                "key": LOCATIONIQ_API_KEY,
                "overview": "false",
                "steps": "false",
            },
            timeout=10,
        )
        if response.status_code != 200:
            return f"⚠️ خطأ في حساب المسار: {response.text}"

        routes = response.json().get("routes", [])
        if not routes:
            return "⚠️ لم يتم العثور على مسار بين الموقعين."

        route = routes[0]
        return (
            f"🚗 المسافة بالطريق: {round(route['distance'] / 1000, 1)} كم\n"
            f"⏱️ الوقت المتوقع بالسيارة: {round(route['duration'] / 60, 1)} دقيقة"
        )
    except (KeyError, TypeError, ValueError) as exc:
        return f"⚠️ بيانات المسار غير صالحة: {exc}"
    except requests.RequestException as exc:
        return f"⚠️ تعذر الاتصال بخدمة المسارات: {exc}"
