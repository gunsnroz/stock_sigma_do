#!/usr/bin/env python3
import os, subprocess
from telegram import Update, ParseMode
from telegram.ext import Updater, CommandHandler, CallbackContext

TOKEN  = os.environ['TELEGRAM_TOKEN']
SCRIPT = os.path.join(os.getcwd(), 'sigma_multi.sh')

def sigma(update: Update, context: CallbackContext):
    cmd = [SCRIPT] + context.args
    try:
        res = subprocess.run(
            cmd, check=True, capture_output=True, text=True, env=os.environ
        )
    except subprocess.CalledProcessError as e:
        err = e.stderr or e.stdout
        update.message.reply_text(
            f"⚠️ 오류:\n<pre>{err}</pre>",
            parse_mode=ParseMode.HTML
        )
        return
    output = res.stdout.strip()
    update.message.reply_text(
        f"<pre>{output}</pre>",
        parse_mode=ParseMode.HTML
    )

def main():
    updater = Updater(TOKEN)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('sigma', sigma))
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
