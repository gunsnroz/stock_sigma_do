#!/usr/bin/env python3
import os, sys, smtplib
from email.mime.text import MIMEText

# PAYLOAD를 첫 번째 인자로 받습니다
payload = sys.argv[1]

msg = MIMEText(payload, _charset='utf-8')
msg['Subject'] = "매수 단가 알림"
msg['From']    = os.environ['EMAIL_USER']
msg['To']      = os.environ['EMAIL_TO']

smtp = smtplib.SMTP(os.environ['SMTP_HOST'], int(os.environ['SMTP_PORT']))
smtp.starttls()
smtp.login(os.environ['EMAIL_USER'], os.environ['EMAIL_PASS'])
smtp.send_message(msg)
smtp.quit()
