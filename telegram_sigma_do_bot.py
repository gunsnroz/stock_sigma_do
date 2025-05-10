#!/usr/bin/env python3
import os
import subprocess
import html
from io import BytesIO
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
    /sigma command: runs the multi-sigma checker and sends the raw output as a .txt file to avoid wrapping.
    """
    text = run_script(SCRIPT_MULTI, context.args)
    buffer = BytesIO(text.encode('utf-8'))
    buffer.name = "sigma_multi.txt"
    # Send as document to preserve all lines without wrapping
    await update.message.reply_document(
        document=buffer,
        filename=buffer.name,
        caption="📄 Here is your sigma report:",
    )

async def sigma_do(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /sigma_do command: runs the one-shot sigma_do script and sends the raw output as a .txt file.
    """
    output = run_script(SCRIPT_DO, context.args)
    buffer = BytesIO(output.encode('utf-8'))
    buffer.name = "sigma_do.txt"
    await update.message.reply_document(
        document=buffer,
        filename=buffer.name,
        caption="📄 Here is your sigma_do output:",
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
