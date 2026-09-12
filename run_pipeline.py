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


작업 지시:

원인을 분석하여 '{MAIN_SCRIPT}'의 코드를 정상 작동하도록 수정하세요.

수정 내역, 원인, 대책을 정리하여 '{REPORT_FILE}' 파일에 마크다운 형식의 보고서로 작성하세요.
"""

LiteLLM 포맷을 사용하여 Gemini API 모델 지정
cmd = [
"aider",
"--model",
"gemini/gemini-2.5-flash",
"--file",
MAIN_SCRIPT,
"--file",
REPORT_FILE,
"--message",
prompt,
"--no-auto-commits",
]

print("🤖 오류 발생! aider를 실행하여 자동 디버깅을 시도합니다...")
subprocess.run(cmd)

def main():
returncode, stdout, stderr = run_main_script()

if returncode == 0:
    print("✅ 추천 스크립트가 성공적으로 수행되었습니다.")
else:
    error_msg = stderr if stderr else stdout
    print(f"❌ 스크립트 실행 에러 발생:\n{error_msg}")

    # 1. aider 디버그 수행
    run_aider_auto_debug(error_msg)

    # 2. 작성된 디버그 보고서 텔레그램 전송
    if os.path.exists(REPORT_FILE):
        with open(REPORT_FILE, "r", encoding="utf-8") as f:
            report_text = f.read()
        send_telegram(
            f"⚠️ **코디 추천 실행 오류 발생 (자동 디버그 완료)**\n\n{report_text}"
        )
    else:
        send_telegram(
            f"⚠️ **코디 추천 실행 오류 발생**\n```text\n{error_msg[:1000]}\n```"
        )

    # GitHub Actions에 실패 상태 전달
    sys.exit(1)
if name == "main":
main()
