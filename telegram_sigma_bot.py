#!/usr/bin/env python3
import os
import subprocess
from telegram import Update, ParseMode
from telegram.ext import Updater, CommandHandler, CallbackContext

TOKEN = os.environ['TELEGRAM_TOKEN']

def sigma(update: Update, context: CallbackContext):
    args = context.args
    script = os.path.join(os.getcwd(), 'sigma_multi.sh')
    if len(args) == 2:
        cmd = [script, args[0], args[1]]
    else:
        cmd = [script]
    try:
        res = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            env=os.environ
        )
        output = res.stdout.strip()
    except subprocess.CalledProcessError as e:
        update.message.reply_text(
            f"⚠️ 스크립트 실행 오류:\n```\n{e.stderr.strip()}\n```",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    update.message.reply_text(
        f"```\n{output}\n```",
        parse_mode=ParseMode.MARKDOWN
    )

def main():
    updater = Updater(TOKEN)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('sigma', sigma))
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
