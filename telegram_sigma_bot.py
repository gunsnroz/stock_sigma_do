#!/usr/bin/env python3
import os
import subprocess
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

SCRIPT_MULTI = "sigma_multi.sh"
SCRIPT_DO    = "sigma_do.sh"

def run_script(script_name: str, args: list[str]) -> str:
    script_path = os.path.join(os.path.dirname(__file__), script_name)
    result = subprocess.run(
        [script_path] + args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        shell=False
    )
    return result.stdout or result.stderr

async def sigma(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = run_script(SCRIPT_MULTI, context.args)
    await update.message.reply_text(
        f"<pre>{text}</pre>",
        parse_mode="HTML",
        disable_web_page_preview=True
    )

async def sigma_do(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = run_script(SCRIPT_DO, context.args)
    await update.message.reply_text(
        f"<pre>{text}</pre>",
        parse_mode="HTML",
        disable_web_page_preview=True
    )

def main():
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        raise RuntimeError("환경변수 TELEGRAM_TOKEN 이 설정되어 있지 않습니다.")
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("sigma", sigma))
    app.add_handler(CommandHandler("sigma.do", sigma_do))
    app.run_polling()

if __name__ == "__main__":
    main()
