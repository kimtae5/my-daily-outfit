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
    base_url = "[https://api.openweathermap.org/data/2.5/weather](https://api.openweathermap.org/data/2.5/weather)"
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
            images.append((os.path.basename(path), img))
        except Exception as e:
            print(f"이미지 로드 실패 ({path}): {e}")

    return images


def get_outfit_recommendation(weather_info, clothes_images):
    """Gemini 3.7 Flash를 활용하여 날씨와 사진 기반 착장 추천받기"""
    client = genai.Client(api_key=GEMINI_API_KEY)

    prompt = f"""
너는 패션 감각이 뛰어난 퍼스널 스타일리스트야.
오늘의 날씨 정보와 보유 중인 옷 사진들을 바탕으로 최적의 코디를 추천해 줘.

[오늘의 날씨]
- 도시: {weather_info['city']}
- 현재 기온: {weather_info['temp']}°C (최저 {weather_info['temp_min']}°C / 최고 {weather_info['temp_max']}°C)
- 날씨 상태: {weather_info['description']}

[지시 사항]
1. 제공된 옷 사진들을 분석하여 종류, 색상, 계절감을 파악해 줘.
2. 오늘 날씨와 온도, 최신 패션 트렌드에 맞는 착장 조합(상의, 하의, 아우터 등)을 추천해 줘.
3. 추천 이유를 기온 변화와 스타일 측면에서 친절하게 설명해 줘.
4. 답변은 텔레그램 메시지로 바로 전송할 수 있게 깔끔하고 읽기 편한 Markdown 형식으로 작성해 줘.
"""

    contents = [prompt]
    for filename, img in clothes_images:
        contents.append(f"파일명: {filename}")
        contents.append(img)

    response = client.models.generate_content(
        model="gemini-3.7-flash", contents=contents
    )

    return response.text


def send_telegram(message):
    """텔레그램 메시지 전송"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        raise ValueError("텔레그램 API 설정이 올바르지 않습니다.")

    url = "[https://api.telegram.org/bot](https://api.telegram.org/bot)" + str(TELEGRAM_BOT_TOKEN) + "/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
    }
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
