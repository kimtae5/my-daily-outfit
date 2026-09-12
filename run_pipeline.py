import os
import subprocess
import sys
import requests

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
MAIN_SCRIPT = "recommend_outfit.py"
REPORT_FILE = "debug_report.md"


def send_telegram(message):
    """텔레그램 메시지 전송"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"텔레그램 전송 실패: {e}")


def run_main_script():
    """추천 스크립트 실행"""
    result = subprocess.run(
        [sys.executable, MAIN_SCRIPT], capture_output=True, text=True
    )
    return result.returncode, result.stdout, result.stderr


def run_aider_auto_debug(error_log):
    """오류 발생 시 aider를 호출하여 코드 수정 및 debug_report.md 생성"""
    prompt = f"""
[자동 디버그 요청]
'{MAIN_SCRIPT}' 실행 중 오류가 발생했습니다.

오류 내용:
```text
{error_log}
