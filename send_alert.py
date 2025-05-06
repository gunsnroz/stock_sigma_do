#!/usr/bin/env python3
import os, sys, smtplib
from email.mime.text import MIMEText

# PAYLOAD 받기
payload = sys.argv[1]

# 환경변수 또는 기본값
host = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
port = int(os.environ.get('SMTP_PORT', 587))

msg = MIMEText(payload, _charset='utf-8')
msg['Subject'] = "매수 단가 알림"
msg['From']    = os.environ['EMAIL_USER']
msg['To']      = os.environ['EMAIL_TO']

with smtplib.SMTP(host, port) as smtp:
    smtp.starttls()
    smtp.login(os.environ['EMAIL_USER'], os.environ['EMAIL_PASS'])
    smtp.send_message(msg)
