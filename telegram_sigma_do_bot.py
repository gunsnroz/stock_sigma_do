#!/usr/bin/env python3
import os
import subprocess
import html
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Shell scripts to run
SCRIPT_MULTI = "sigma_multi.sh"
SCRIPT_DO    = "sigma_do.sh"

def run_script(script_name: str, args: list[str]) -> str:
    """
    Executes a shell script and returns either stdout or stderr as text.
    """
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
    """
    /sigma command: runs the multi-sigma checker and returns formatted output.
    """
    text = run_script(SCRIPT_MULTI, context.args)
    safe = html.escape(text)
    # Use HTML <pre> block to preserve long lines without wrapping
    await update.message.reply_text(
        f"<pre>{safe}</pre>",
        parse_mode="HTML",
        disable_web_page_preview=True,
    )

async def sigma_do(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /sigma_do command: runs the one-shot sigma_do script and returns formatted output.
    """
    output = run_script(SCRIPT_DO, context.args)
    safe = html.escape(output)
    await update.message.reply_text(
        f"<pre>{safe}</pre>",
        parse_mode="HTML",
        disable_web_page_preview=True,
    )

def main():
    # Fetch Telegram bot token from environment
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        raise RuntimeError("환경변수 TELEGRAM_TOKEN 이 설정되어 있지 않습니다.")

    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("sigma", sigma))
    app.add_handler(CommandHandler("sigma_do", sigma_do))
    app.run_polling()

if __name__ == "__main__":
    main()
