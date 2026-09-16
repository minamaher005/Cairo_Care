import math

import requests
from langchain.tools import tool

from config import LOCATIONIQ_API_KEY
from vector_store import get_vector_store


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
        return (
            f"location: {result.get('display_name', location_name)}\n"
            f"latitude: {float(result['lat'])}\n"
            f"longitude: {float(result['lon'])}"
        )
    except (KeyError, TypeError, ValueError) as exc:
        return f"⚠️ بيانات الموقع غير صالحة: {exc}"
    except requests.RequestException as exc:
        return f"⚠️ تعذر الاتصال بخدمة تحديد الموقع: {exc}"


@tool
def find_nearest_hospitals(user_lat: float, user_lon: float, specialty: str = "") -> str:
    """Return the three closest hospitals to coordinates from the local database."""
    try:
        metadata_rows = get_vector_store()._collection.get(include=["metadatas"])["metadatas"]
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
        f"   📞 الهاتف: {hospital['phone']}\n"
        f"   📌 الإحداثيات: {hospital['lat']}, {hospital['lon']}"
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
