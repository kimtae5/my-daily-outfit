import os
import glob
import requests
from PIL import Image
from google import genai

# 환경 변수 로드
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
CITY_NAME = os.getenv("CITY_NAME", "Seoul")


def get_weather():
    """OpenWeatherMap API를 이용해 현재 날씨와 기온 정보 가져오기"""
    if not OPENWEATHER_API_KEY:
        raise ValueError("OPENWEATHER_API_KEY 환경변수가 설정되지 않았습니다.")

    # 순수 URL 문자열 생성
    base_url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": CITY_NAME,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
        "lang": "kr"
    }
    response = requests.get(base_url, params=params, timeout=10)

    if response.status_code != 200:
        raise RuntimeError(f"날씨 API 호출 실패 (상태 코드: {response.status_code})")

    data = response.json()
    temp = data["main"]["temp"]
    temp_min = data["main"]["temp_min"]
    temp_max = data["main"]["temp_max"]
    description = data["weather"][0]["description"]

    return {
        "city": CITY_NAME,
        "temp": temp,
        "temp_min": temp_min,
        "temp_max": temp_max,
        "description": description,
    }


def load_clothes_images():
    """clothes/ 폴더에서 옷 사진 이미지 파일들을 읽어오기"""
    image_paths = (
        glob.glob("clothes/*.jpg")
        + glob.glob("clothes/*.png")
        + glob.glob("clothes/*.jpeg")
    )
    if not image_paths:
        raise FileNotFoundError(
            "clothes/ 폴더 내에 이미지 파일(.jpg, .png)이 존재하지 않습니다."
        )

    images = []
    for path in image_paths:
        try:
            img = Image.open(path)
            images.append((os.basename(path), img))
        except Exception as e:
            print(f"이미지 로드 실패 ({path}): {e}")

    return images


def get_outfit_recommendation(weather_info, clothes_images):
    client = genai.Client(api_key=GEMINI_API_KEY)

    prompt = f"""
너는 퍼스널 스타일리스트야. 
[엄격한 제약조건]
1. 아래 첨부된 옷 사진에 있는 옷들로만 코디를 구성해야 해.
2. 추천하는 상의, 하의, 아우터 등 각 아이템마다 **어떤 이미지 파일(예: `파일명: shirt1.jpg`)에서 가져온 것인지 파일명을 반드시 정확히 명시**해 줘.
3. 사진에 없는 새로운 옷을 임의로 만들어내서 추천하지 마.

[오늘의 날씨]
- 도시: {weather_info['city']}
- 현재 기온: {weather_info['temp']}°C (최저 {weather_info['temp_min']}°C / 최고 {weather_info['temp_max']}°C)
- 날씨 상태: {weather_info['description']}

[출력 형식 예시]
- 상의: [파일명: top_blue.jpg] 파란색 셔츠
- 하의: [파일명: pants_black.jpg] 검은색 슬랙스
- 추천 이유: ...
"""

    contents = [prompt]
    for filename, img in clothes_images:
        contents.append(f"파일명: {filename}")
        contents.append(img)

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite", contents=contents
    )

    return response.text


def send_telegram(message):
    """텔레그램 메시지 전송"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        raise ValueError("텔레그램 API 설정이 올바르지 않습니다.")

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    # 1차 시도: Markdown 파싱 전송
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
    }
    res = requests.post(url, json=payload, timeout=10)

    # 마크다운 구문 오류(400 Bad Request) 발생 시 parse_mode를 제거하여 일반 텍스트로 재시도
    if res.status_code == 400 and "can't parse entities" in res.text:
        print("⚠️ 텔레그램 마크다운 파싱 오류 발생. 일반 텍스트 모드로 재시도합니다.")
        payload.pop("parse_mode")
        res = requests.post(url, json=payload, timeout=10)

    if res.status_code != 200:
        raise RuntimeError(f"텔레그램 전송 실패: {res.text}")


def main():
    print("🌤️ 날씨 정보를 불러오는 중...")
    weather = get_weather()

    print("👕 옷 사진 데이터를 읽는 중...")
    clothes = load_clothes_images()

    print("🤖 Gemini AI 코디 분석 중...")
    recommendation = get_outfit_recommendation(weather, clothes)

    print("📱 텔레그램 메시지 전송 중...")
    send_telegram(recommendation)
    print("✅ 착장 추천 및 전송이 완료되었습니다!")


if __name__ == "__main__":
    main()
