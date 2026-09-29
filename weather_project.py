"""터미널에서 도시의 현재 날씨와 오늘 예보를 보여 주는 프로그램."""

from __future__ import annotations

import json
import sys
from datetime import datetime
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

WEATHER_CODES = {
    0: "맑음",
    1: "대체로 맑음",
    2: "약간 흐림",
    3: "흐림",
    45: "안개",
    48: "서리 안개",
    51: "약한 이슬비",
    53: "이슬비",
    55: "강한 이슬비",
    56: "약한 어는 이슬비",
    57: "강한 어는 이슬비",
    61: "약한 비",
    63: "비",
    65: "강한 비",
    66: "약한 어는 비",
    67: "강한 어는 비",
    71: "약한 눈",
    73: "눈",
    75: "강한 눈",
    77: "싸락눈",
    80: "약한 소나기",
    81: "소나기",
    82: "강한 소나기",
    85: "약한 눈 소나기",
    86: "강한 눈 소나기",
    95: "뇌우",
    96: "약한 우박을 동반한 뇌우",
    99: "강한 우박을 동반한 뇌우",
}


def get_json(url: str, params: dict[str, str | float]) -> dict:
    """공개 API에서 JSON 응답을 받아온다."""
    request = Request(
        f"{url}?{urlencode(params)}",
        headers={"User-Agent": "terminal-weather-program/1.0"},
    )
    with urlopen(request, timeout=10) as response:
        return json.load(response)


def find_city(city: str) -> dict | None:
    data = get_json(
        GEOCODING_URL,
        {"name": city, "count": "1", "language": "ko", "format": "json"},
    )
    results = data.get("results", [])
    return results[0] if results else None


def get_weather(latitude: float, longitude: float) -> dict:
    return get_json(
        FORECAST_URL,
        {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,apparent_temperature,relative_humidity_2m,precipitation,weather_code,wind_speed_10m",
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
            "timezone": "auto",
            "forecast_days": "1",
        },
    )


def print_weather(city_info: dict, weather: dict) -> None:
    current = weather["current"]
    daily = weather["daily"]
    city_name = city_info["name"]
    country = city_info.get("country", "")
    timestamp = datetime.fromisoformat(current["time"])
    condition = WEATHER_CODES.get(current["weather_code"], "알 수 없음")
    today_condition = WEATHER_CODES.get(daily["weather_code"][0], "알 수 없음")

    print("\n" + "=" * 42)
    print(f"  {city_name} ({country}) 날씨")
    print("=" * 42)
    print(f"  기준 시각 : {timestamp:%Y-%m-%d %H:%M}")
    print(f"  현재 날씨 : {condition}")
    print(f"  현재 기온 : {current['temperature_2m']:.1f}°C")
    print(f"  체감 기온 : {current['apparent_temperature']:.1f}°C")
    print(f"  습도      : {current['relative_humidity_2m']}%")
    print(f"  강수량    : {current['precipitation']:.1f} mm")
    print(f"  풍속      : {current['wind_speed_10m']:.1f} km/h")
    print("-" * 42)
    print(f"  오늘 예보 : {today_condition}")
    print(f"  최저/최고 : {daily['temperature_2m_min'][0]:.1f}°C / {daily['temperature_2m_max'][0]:.1f}°C")
    print(f"  최대 강수확률: {daily['precipitation_probability_max'][0]}%")
    print("=" * 42)


def main() -> None:
    print("터미널 날씨 정보")
    print("종료하려면 q를 입력하세요.")

    while True:
        city = input("\n도시 이름을 입력하세요 (예: 서울, Busan): ").strip()
        if city.lower() in {"q", "quit", "exit", "종료"}:
            print("날씨 프로그램을 종료합니다.")
            return
        if not city:
            print("도시 이름을 입력해 주세요.")
            continue

        try:
            city_info = find_city(city)
            if city_info is None:
                print(f"'{city}'의 위치 정보를 찾지 못했습니다. 다른 이름으로 입력해 주세요.")
                continue
            weather = get_weather(city_info["latitude"], city_info["longitude"])
            print_weather(city_info, weather)
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as error:
            print(f"날씨 정보를 가져오지 못했습니다: {error}")
        except KeyboardInterrupt:
            print("\n날씨 프로그램을 종료합니다.")
            return


if __name__ == "__main__":
    try:
        main()
    except EOFError:
        print("\n입력이 종료되어 프로그램을 마칩니다.")
        sys.exit(0)
