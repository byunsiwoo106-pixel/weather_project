"""터미널에서 도시의 현재 날씨와 3일 예보를 보여 주는 프로그램."""

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

WEEKDAYS = ("월", "화", "수", "목", "금", "토", "일")

# Open-Meteo 위치 검색은 일부 한글 도시명을 찾지 못할 수 있어 영문 검색어로 바꾼다.
KOREAN_CITY_NAMES = {
    "서울": "Seoul",
    "서울특별시": "Seoul",
    "부산": "Busan",
    "부산광역시": "Busan",
    "대구": "Daegu",
    "대구광역시": "Daegu",
    "인천": "Incheon",
    "인천광역시": "Incheon",
    "광주": "Gwangju",
    "광주광역시": "Gwangju",
    "대전": "Daejeon",
    "대전광역시": "Daejeon",
    "울산": "Ulsan",
    "울산광역시": "Ulsan",
    "세종": "Sejong",
    "세종특별자치시": "Sejong",
    "수원": "Suwon",
    "성남": "Seongnam",
    "고양": "Goyang",
    "용인": "Yongin",
    "춘천": "Chuncheon",
    "강릉": "Gangneung",
    "청주": "Cheongju",
    "천안": "Cheonan",
    "전주": "Jeonju",
    "목포": "Mokpo",
    "포항": "Pohang",
    "창원": "Changwon",
    "제주": "Jeju City",
    "제주시": "Jeju City",
    "서귀포": "Seogwipo",
}


def get_weather_emoji(weather_code: int) -> str:
    """WMO 날씨 코드에 맞는 이모지를 돌려준다."""
    if weather_code == 0:
        return "☀️"
    if weather_code == 1:
        return "🌤️"
    if weather_code == 2:
        return "⛅"
    if weather_code == 3:
        return "☁️"
    if weather_code in {45, 48}:
        return "🌫️"
    if weather_code in {51, 53, 55, 56, 57}:
        return "🌦️"
    if weather_code in {61, 63, 65, 66, 67, 80, 81, 82}:
        return "🌧️"
    if weather_code in {71, 73, 75, 77}:
        return "❄️"
    if weather_code in {85, 86}:
        return "🌨️"
    if weather_code == 95:
        return "🌩️"
    if weather_code in {96, 99}:
        return "⛈️"
    return "🌡️"


def get_json(url: str, params: dict[str, str | float]) -> dict:
    """공개 API에서 JSON 응답을 받아온다."""
    request = Request(
        f"{url}?{urlencode(params)}",
        headers={"User-Agent": "terminal-weather-program/1.0"},
    )
    with urlopen(request, timeout=10) as response:
        return json.load(response)


def find_city(city: str) -> dict | None:
    search_name = KOREAN_CITY_NAMES.get(city, city)
    data = get_json(
        GEOCODING_URL,
        {
            "name": search_name,
            "count": "1",
            "language": "ko",
            "format": "json",
            "countryCode": "KR",
        },
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
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,precipitation_sum,wind_speed_10m_max,uv_index_max,sunrise,sunset",
            "hourly": "temperature_2m,weather_code,precipitation_probability",
            "timezone": "auto",
            "forecast_days": "3",
        },
    )


def print_weather(city_info: dict, weather: dict) -> None:
    current = weather["current"]
    daily = weather["daily"]
    hourly = weather["hourly"]
    city_name = city_info["name"]
    timestamp = datetime.fromisoformat(current["time"])
    condition = WEATHER_CODES.get(current["weather_code"], "알 수 없음")
    current_emoji = get_weather_emoji(current["weather_code"])

    hourly_by_time = {
        time: (temperature, weather_code, rain_chance)
        for time, temperature, weather_code, rain_chance in zip(
            hourly["time"],
            hourly["temperature_2m"],
            hourly["weather_code"],
            hourly["precipitation_probability"],
        )
    }

    print("\n" + "=" * 58)
    print(f"  {city_name} (대한민국) 날씨")
    print("=" * 58)
    print(f"  기준 시각 : {timestamp:%Y-%m-%d %H:%M}")
    print(f"  현재 날씨 : {current_emoji} {condition}")
    print(f"  현재 기온 : {current['temperature_2m']:.1f}°C")
    print(f"  체감 기온 : {current['apparent_temperature']:.1f}°C")
    print(f"  습도      : {current['relative_humidity_2m']}%")
    print(f"  강수량    : {current['precipitation']:.1f} mm")
    print(f"  풍속      : {current['wind_speed_10m']:.1f} km/h")
    print("-" * 58)
    print("  상세 3일 예보")
    for index, date_text in enumerate(daily["time"]):
        date = datetime.fromisoformat(date_text)
        day_name = "오늘" if index == 0 else "내일" if index == 1 else "모레"
        weather_code = daily["weather_code"][index]
        condition = WEATHER_CODES.get(weather_code, "알 수 없음")
        emoji = get_weather_emoji(weather_code)
        low = daily["temperature_2m_min"][index]
        high = daily["temperature_2m_max"][index]
        rain_chance = daily["precipitation_probability_max"][index]
        rain_sum = daily["precipitation_sum"][index]
        max_wind = daily["wind_speed_10m_max"][index]
        max_uv = daily["uv_index_max"][index]
        sunrise = datetime.fromisoformat(daily["sunrise"][index])
        sunset = datetime.fromisoformat(daily["sunset"][index])

        print(f"  {day_name} ({date:%m/%d} {WEEKDAYS[date.weekday()]}): {emoji} {condition}")
        print(f"    최저/최고 {low:.1f}°C / {high:.1f}°C | 강수확률 {rain_chance}%")
        print(f"    예상 강수량 {rain_sum:.1f} mm | 최대 풍속 {max_wind:.1f} km/h | 최대 UV {max_uv:.1f}")
        print(f"    일출 {sunrise:%H:%M} | 일몰 {sunset:%H:%M}")

        for label, hour in (("오전", 9), ("오후", 15), ("밤", 21)):
            period = hourly_by_time.get(f"{date_text}T{hour:02d}:00")
            if period is None:
                continue
            period_temp, period_code, period_rain_chance = period
            period_condition = WEATHER_CODES.get(period_code, "알 수 없음")
            period_emoji = get_weather_emoji(period_code)
            print(
                f"    {label} {hour:02d}시: {period_emoji} {period_condition}, "
                f"{period_temp:.1f}°C, 강수확률 {period_rain_chance}%"
            )
        print("-" * 58)
    print("=" * 58)


def main() -> None:
    print("터미널 날씨 정보")
    print("종료하려면 q를 입력하세요.")

    while True:
        city = input("\n대한민국 도시 이름을 입력하세요 (예: 서울, 부산): ").strip()
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
