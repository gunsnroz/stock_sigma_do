#!/usr/bin/env python3
import os, requests, smtplib
import yfinance as yf
import pandas as pd
from email.mime.text import MIMEText
from email.utils import formataddr

def send_telegram(msg):
    r = requests.post(
        f"https://api.telegram.org/bot{os.environ['TELEGRAM_TOKEN']}/sendMessage",
        json={"chat_id": os.environ['TELEGRAM_CHAT_ID'], "text": msg}
    )
    print("📨 Telegram status", r.status_code)

def send_email(subject, body):
    user, pwd = os.environ['EMAIL_USER'], os.environ['EMAIL_PASS']
    to = os.environ['EMAIL_TO']
    m = MIMEText(body, _charset='utf-8')
    m['Subject'] = subject
    m['From']    = formataddr(("Sigma Alert", user))
    m['To']      = to
    s = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    s.login(user, pwd)
    s.sendmail(user, [to], m.as_string())
    s.quit()
    print("📧 Email sent to", to)

def check_std_buy_signal_auto(tickers, period=20, k1=1, k2=2):
    results = []
    for t in tickers:
        df = yf.download(t, period=f"{period*3}d", progress=False)[['Close']].copy()
        df['MA']  = df['Close'].rolling(window=period).mean()
        df['STD'] = df['Close'].rolling(window=period).std()
        df = df.dropna()
        last = df.iloc[-1]
        # 여기에서 float 캐스팅
        price = float(last['Close'])
        ma    = float(last['MA'])
        std   = float(last['STD'])
        l1    = float(ma - k1 * std)
        l2    = float(ma - k2 * std)

        if price < l2:
            sig = "매수(2σ 이하)"
        elif price < l1:
            sig = "매수(1σ 이하)"
        else:
            sig = "대기"

        results.append({
            "Ticker": t,
            "현재가": round(price,2),
            f"{period}일 MA": round(ma,2),
            f"{period}일 1σ": round(l1,2),
            f"{period}일 2σ": round(l2,2),
            "신호": sig
        })
    return pd.DataFrame(results)

if __name__=="__main__":
    tickers = ["SOXL","SCHD","JEPI","JEPQ","QQQ","SPLG","TMF","NVDA"]
    df20  = check_std_buy_signal_auto(tickers, 20)
    df252 = check_std_buy_signal_auto(tickers, 252)
    hdr20  = "===== 20일(1개월) 기준 매수 신호 ====="
    hdr252 = "===== 252일(1년) 기준 매수 신호 ====="
    body = "\n".join([hdr20, df20.to_string(index=False), "", hdr252, df252.to_string(index=False)])
    print(body)
    send_telegram(body)
    send_email("Sigma Buy Signals", body)
