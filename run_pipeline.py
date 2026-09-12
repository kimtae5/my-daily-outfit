import os
import subprocess
import sys
import requests

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
MAIN_SCRIPT = "recommend_outfit.py"
REPORT_FILE = "debug_report.md"

BT3 = "```"


def send_telegram(message):
    """텔레그램 메시지 전송 함수"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ 텔레그램 토큰 또는 Chat ID가 설정되지 않아 알림 전송을 건너뜁니다.")
        return

    # 순수 f-string으로 URL 구성 (마크다운 대괄호 방지)
    url = f"[https://api.telegram.org/bot](https://api.telegram.org/bot){TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
    }
    try:
        res = requests.post(url, json=payload, timeout=10)
        if res.status_code != 200:
            print(f"⚠️ 텔레그램 전송 응답 오류: {res.text}")
    except Exception as e:
        print(f"⚠️ 텔레그램 전송 중 예외 발생: {e}")


def run_main_script():
    """추천 스크립트(recommend_outfit.py) 실행 및 결과/에러 로그 캡처"""
    result = subprocess.run(
        [sys.executable, MAIN_SCRIPT],
        capture_output=True,
        text=True
    )
    return result.returncode, result.stdout, result.stderr


def run_aider_auto_debug(error_log):
    """오류 발생 시 aider를 비대화형 모드로 호출하여 코드 자동 수정 및 보고서 작성"""
    prompt = f"""
[자동 디버그 요청]
'{MAIN_SCRIPT}' 실행 중 다음 오류가 발생했습니다.

오류 로그:
{BT3}text
{error_log}
{BT3}

작업 지시사항:
1. 원인을 분석하여 '{MAIN_SCRIPT}' 파일의 코드를 정상적으로 동작하도록 수정하세요.
2. 에러 원인, 수정 사항, 재발 방지책을 정리하여 '{REPORT_FILE}' 파일에 상세한 Markdown 보고서로 작성하세요.
"""

    # aider 명령어 작성 (--api-key 및 --yes 명시)
    cmd = [
        "aider",
        "--model", "gemini/gemini-3.7-flash",
        "--api-key", f"gemini={GEMINI_API_KEY}",
        "--yes",
        MAIN_SCRIPT,
        REPORT_FILE,
        "--message", prompt,
        "--no-auto-commits"
    ]

    print("\n🤖 [Pipeline] 스크립트 오류 발생! aider를 실행하여 자동 디버깅을 시작합니다...")
    
    # 환경변수 전달
    env = os.environ.copy()
    if GEMINI_API_KEY:
        env["GEMINI_API_KEY"] = GEMINI_API_KEY

    subprocess.run(cmd, env=env)


def main():
    returncode, stdout, stderr = run_main_script()

    if returncode == 0:
        print("✅ [Pipeline] 추천 스크립트가 성공적으로 수행되었습니다.")
    else:
        error_msg = stderr.strip() if stderr.strip() else stdout.strip()
        print(f"❌ [Pipeline] 스크립트 실행 실패!\n--- Error Log ---\n{error_msg}\n-----------------")

        # 1. 오류 발생 시 주 스크립트 자동 디버깅 및 보고서 생성
        run_aider_auto_debug(error_msg)

        # 2. 디버그 보고서 확인 및 텔레그램 알림 전송
        if os.path.exists(REPORT_FILE):
            with open(REPORT_FILE, "r", encoding="utf-8") as f:
                report_text = f.read()
            send_telegram(
                f"⚠️ **[Auto-Debug 완료 알림]**\n"
                f"착장 추천 실행 중 오류가 발생하여 자동 디버깅을 완료했습니다.\n\n"
                f"{report_text}"
            )
        else:
            send_telegram(
                f"⚠️ **[Auto-Debug 오류 알림]**\n"
                f"스크립트 실행 실패 후 보고서 생성에 실패했습니다.\n\n"
                f"오류 내용:\n{BT3}text\n{error_msg[:1000]}\n{BT3}"
            )

        sys.exit(1)


if __name__ == "__main__":
    main()
