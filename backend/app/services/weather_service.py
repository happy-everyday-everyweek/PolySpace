from typing import Optional

import httpx

OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
OPEN_METEO_GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
OPEN_METEO_AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

CURRENT_PARAMS = "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m,wind_direction_10m,surface_pressure,cloud_cover,is_day"
DAILY_PARAMS = "weather_code,temperature_2m_max,temperature_2m_min,apparent_temperature_max,apparent_temperature_min,sunrise,sunset,uv_index_max,precipitation_sum,precipitation_probability_max,wind_speed_10m_max"
HOURLY_PARAMS = "temperature_2m,precipitation_probability,weather_code,wind_speed_10m,uv_index"
AIR_QUALITY_PARAMS = "pm2_5,pm10,us_aqi"

WMO_CODE_MAP = {
    0: {"label": "晴", "label_en": "Clear sky", "icon": "clear"},
    1: {"label": "大部晴朗", "label_en": "Mainly clear", "icon": "mostly-clear"},
    2: {"label": "多云", "label_en": "Partly cloudy", "icon": "partly-cloudy"},
    3: {"label": "阴天", "label_en": "Overcast", "icon": "overcast"},
    45: {"label": "雾", "label_en": "Fog", "icon": "fog"},
    48: {"label": "冻雾", "label_en": "Depositing rime fog", "icon": "fog"},
    51: {"label": "小毛毛雨", "label_en": "Light drizzle", "icon": "drizzle"},
    53: {"label": "中毛毛雨", "label_en": "Moderate drizzle", "icon": "drizzle"},
    55: {"label": "大毛毛雨", "label_en": "Dense drizzle", "icon": "drizzle"},
    56: {"label": "冻毛毛雨", "label_en": "Light freezing drizzle", "icon": "freezing-drizzle"},
    57: {"label": "冻毛毛雨", "label_en": "Dense freezing drizzle", "icon": "freezing-drizzle"},
    61: {"label": "小雨", "label_en": "Slight rain", "icon": "rain"},
    63: {"label": "中雨", "label_en": "Moderate rain", "icon": "rain"},
    65: {"label": "大雨", "label_en": "Heavy rain", "icon": "heavy-rain"},
    66: {"label": "冻雨", "label_en": "Light freezing rain", "icon": "freezing-rain"},
    67: {"label": "冻雨", "label_en": "Heavy freezing rain", "icon": "freezing-rain"},
    71: {"label": "小雪", "label_en": "Slight snowfall", "icon": "snow"},
    73: {"label": "中雪", "label_en": "Moderate snowfall", "icon": "snow"},
    75: {"label": "大雪", "label_en": "Heavy snowfall", "icon": "heavy-snow"},
    77: {"label": "雪粒", "label_en": "Snow grains", "icon": "snow"},
    80: {"label": "小阵雨", "label_en": "Slight rain showers", "icon": "rain-showers"},
    81: {"label": "中阵雨", "label_en": "Moderate rain showers", "icon": "rain-showers"},
    82: {"label": "大阵雨", "label_en": "Violent rain showers", "icon": "heavy-rain-showers"},
    85: {"label": "小阵雪", "label_en": "Slight snow showers", "icon": "snow-showers"},
    86: {"label": "大阵雪", "label_en": "Heavy snow showers", "icon": "snow-showers"},
    95: {"label": "雷暴", "label_en": "Thunderstorm", "icon": "thunderstorm"},
    96: {"label": "雷暴伴冰雹", "label_en": "Thunderstorm with slight hail", "icon": "thunderstorm-hail"},
    99: {"label": "雷暴伴冰雹", "label_en": "Thunderstorm with heavy hail", "icon": "thunderstorm-hail"},
}

WIND_DIR_MAP = [
    "北", "东北偏北", "东北", "东北偏东",
    "东", "东南偏东", "东南", "东南偏南",
    "南", "西南偏南", "西南", "西南偏西",
    "西", "西北偏西", "西北", "西北偏北",
]


def _wind_direction_label(degrees: float) -> str:
    idx = round(degrees / 22.5) % 16
    return WIND_DIR_MAP[idx]


def _weather_code_info(code: int) -> dict:
    return WMO_CODE_MAP.get(code, {"label": "未知", "label_en": "Unknown", "icon": "unknown"})


class WeatherService:
    def __init__(self):
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=15.0)
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def search_city(self, name: str, count: int = 5, language: str = "zh") -> list[dict]:
        client = await self._get_client()
        resp = await client.get(OPEN_METEO_GEOCODING_URL, params={
            "name": name,
            "count": count,
            "language": language,
        })
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results") or []
        return [
            {
                "id": r.get("id"),
                "name": r.get("name", ""),
                "latitude": r.get("latitude"),
                "longitude": r.get("longitude"),
                "country": r.get("country", ""),
                "country_code": r.get("country_code", ""),
                "admin1": r.get("admin1", ""),
                "timezone": r.get("timezone", ""),
            }
            for r in results
        ]

    async def get_current_weather(self, latitude: float, longitude: float) -> dict:
        client = await self._get_client()
        resp = await client.get(OPEN_METEO_FORECAST_URL, params={
            "latitude": latitude,
            "longitude": longitude,
            "current": CURRENT_PARAMS,
            "timezone": "auto",
        })
        resp.raise_for_status()
        data = resp.json()
        current = data.get("current", {})
        code = current.get("weather_code", 0)
        info = _weather_code_info(code)
        wind_dir = current.get("wind_direction_10m", 0)
        return {
            "latitude": data.get("latitude"),
            "longitude": data.get("longitude"),
            "timezone": data.get("timezone"),
            "current": {
                "time": current.get("time"),
                "temperature": current.get("temperature_2m"),
                "feels_like": current.get("apparent_temperature"),
                "humidity": current.get("relative_humidity_2m"),
                "precipitation": current.get("precipitation"),
                "weather_code": code,
                "weather_label": info["label"],
                "weather_label_en": info["label_en"],
                "weather_icon": info["icon"],
                "wind_speed": current.get("wind_speed_10m"),
                "wind_direction": wind_dir,
                "wind_direction_label": _wind_direction_label(wind_dir),
                "pressure": current.get("surface_pressure"),
                "cloud_cover": current.get("cloud_cover"),
                "is_day": current.get("is_day"),
            },
        }

    async def get_forecast(
        self,
        latitude: float,
        longitude: float,
        forecast_days: int = 7,
    ) -> dict:
        client = await self._get_client()
        resp = await client.get(OPEN_METEO_FORECAST_URL, params={
            "latitude": latitude,
            "longitude": longitude,
            "current": CURRENT_PARAMS,
            "daily": DAILY_PARAMS,
            "hourly": HOURLY_PARAMS,
            "timezone": "auto",
            "forecast_days": forecast_days,
        })
        resp.raise_for_status()
        data = resp.json()
        current_raw = data.get("current", {})
        daily_raw = data.get("daily", {})
        hourly_raw = data.get("hourly", {})

        code = current_raw.get("weather_code", 0)
        info = _weather_code_info(code)
        wind_dir = current_raw.get("wind_direction_10m", 0)

        current = {
            "time": current_raw.get("time"),
            "temperature": current_raw.get("temperature_2m"),
            "feels_like": current_raw.get("apparent_temperature"),
            "humidity": current_raw.get("relative_humidity_2m"),
            "precipitation": current_raw.get("precipitation"),
            "weather_code": code,
            "weather_label": info["label"],
            "weather_label_en": info["label_en"],
            "weather_icon": info["icon"],
            "wind_speed": current_raw.get("wind_speed_10m"),
            "wind_direction": wind_dir,
            "wind_direction_label": _wind_direction_label(wind_dir),
            "pressure": current_raw.get("surface_pressure"),
            "cloud_cover": current_raw.get("cloud_cover"),
            "is_day": current_raw.get("is_day"),
        }

        daily_times = daily_raw.get("time", [])
        daily = []
        for i, t in enumerate(daily_times):
            d_code = daily_raw.get("weather_code", [])[i] if i < len(daily_raw.get("weather_code", [])) else 0
            d_info = _weather_code_info(d_code)
            daily.append({
                "date": t,
                "weather_code": d_code,
                "weather_label": d_info["label"],
                "weather_label_en": d_info["label_en"],
                "weather_icon": d_info["icon"],
                "temp_max": daily_raw.get("temperature_2m_max", [])[i] if i < len(daily_raw.get("temperature_2m_max", [])) else None,
                "temp_min": daily_raw.get("temperature_2m_min", [])[i] if i < len(daily_raw.get("temperature_2m_min", [])) else None,
                "feels_like_max": daily_raw.get("apparent_temperature_max", [])[i] if i < len(daily_raw.get("apparent_temperature_max", [])) else None,
                "feels_like_min": daily_raw.get("apparent_temperature_min", [])[i] if i < len(daily_raw.get("apparent_temperature_min", [])) else None,
                "sunrise": daily_raw.get("sunrise", [])[i] if i < len(daily_raw.get("sunrise", [])) else None,
                "sunset": daily_raw.get("sunset", [])[i] if i < len(daily_raw.get("sunset", [])) else None,
                "uv_index": daily_raw.get("uv_index_max", [])[i] if i < len(daily_raw.get("uv_index_max", [])) else None,
                "precipitation_sum": daily_raw.get("precipitation_sum", [])[i] if i < len(daily_raw.get("precipitation_sum", [])) else None,
                "precipitation_probability": daily_raw.get("precipitation_probability_max", [])[i] if i < len(daily_raw.get("precipitation_probability_max", [])) else None,
                "wind_speed_max": daily_raw.get("wind_speed_10m_max", [])[i] if i < len(daily_raw.get("wind_speed_10m_max", [])) else None,
            })

        hourly_times = hourly_raw.get("time", [])
        hourly = []
        for i, t in enumerate(hourly_times):
            h_code = hourly_raw.get("weather_code", [])[i] if i < len(hourly_raw.get("weather_code", [])) else 0
            h_info = _weather_code_info(h_code)
            hourly.append({
                "time": t,
                "temperature": hourly_raw.get("temperature_2m", [])[i] if i < len(hourly_raw.get("temperature_2m", [])) else None,
                "precipitation_probability": hourly_raw.get("precipitation_probability", [])[i] if i < len(hourly_raw.get("precipitation_probability", [])) else None,
                "weather_code": h_code,
                "weather_label": h_info["label"],
                "weather_icon": h_info["icon"],
                "wind_speed": hourly_raw.get("wind_speed_10m", [])[i] if i < len(hourly_raw.get("wind_speed_10m", [])) else None,
                "uv_index": hourly_raw.get("uv_index", [])[i] if i < len(hourly_raw.get("uv_index", [])) else None,
            })

        return {
            "latitude": data.get("latitude"),
            "longitude": data.get("longitude"),
            "timezone": data.get("timezone"),
            "current": current,
            "daily": daily,
            "hourly": hourly,
        }

    async def get_air_quality(self, latitude: float, longitude: float) -> dict:
        client = await self._get_client()
        resp = await client.get(OPEN_METEO_AIR_QUALITY_URL, params={
            "latitude": latitude,
            "longitude": longitude,
            "current": AIR_QUALITY_PARAMS,
            "timezone": "auto",
        })
        resp.raise_for_status()
        data = resp.json()
        current = data.get("current", {})
        return {
            "pm2_5": current.get("pm2_5"),
            "pm10": current.get("pm10"),
            "us_aqi": current.get("us_aqi"),
        }


weather_service = WeatherService()
