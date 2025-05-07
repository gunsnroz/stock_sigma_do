#!/usr/bin/env python3
import os
import subprocess
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# 환경 변수로부터 토큰과 스크립트 경로 가져오기
TOKEN        = os.getenv("TELEGRAM_TOKEN")
CHAT_ID      = None  # 필요하다면 기본 chat_id를 여기에 설정
SCRIPT_PATH  = os.path.join(os.path.dirname(__file__), "sigma_multi.sh")

def send_sigma(update: Update, context: CallbackContext):
    """/sigma [YYMMDD YYMMDD] 명령 처리"""
    args = context.args
    # 스크립트 호출 인자 설정
    if len(args) == 2:
        cmd = [SCRIPT_PATH, args[0], args[1]]
    else:
        cmd = [SCRIPT_PATH]

    # 스크립트 실행
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    output = proc.stdout or proc.stderr

    # HTML <pre> 로 감싸서 고정폭 전달
    html = f"<pre>{output}</pre>"
    update.message.reply_text(
        html,
        parse_mode="HTML",
        disable_web_page_preview=True,
    )

def main():
    updater = Updater(TOKEN)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("sigma", send_sigma))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
