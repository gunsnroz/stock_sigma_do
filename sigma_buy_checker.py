#!/usr/bin/env python3
import os
import requests
import smtplib
import yfinance as yf
import pandas as pd
from email.mime.text import MIMEText
from email.utils import formataddr

# —————————————————————————————————————
# 주문 · 알림용 함수
def send_telegram(msg: str):
    token   = os.environ['TELEGRAM_TOKEN']
    chat_id = os.environ['TELEGRAM_CHAT_ID']
    url     = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": msg})

def send_email(subject: str, body: str):
    user = os.environ['EMAIL_USER']
    pwd  = os.environ['EMAIL_PASS']
    to   = os.environ['EMAIL_TO']
    m    = MIMEText(body, _charset='utf-8')
    m['Subject'] = subject
    m['From']    = formataddr(("Sigma Alert", user))
    m['To']      = to

    s = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    s.login(user, pwd)
    s.sendmail(user, [to], m.as_string())
    s.quit()
# —————————————————————————————————————

def check_std_buy_signal_auto(tickers, period=20, k1=1, k2=2):
    results = []
    for ticker in tickers:
        df = yf.download(ticker, period=f"{period*3}d", progress=False)[['Close']].copy()
        df['MA']  = df['Close'].rolling(window=period).mean()
        df['STD'] = df['Close'].rolling(window=period).std()
        df = df.dropna().iloc[-1]
        price, ma, std = df['Close'], df['MA'], df['STD']
        l1, l2 = ma - k1*std, ma - k2*std

        if price < l2:  sig = "매수(2σ 이하)"
        elif price < l1: sig = "매수(1σ 이하)"
        else:            sig = "대기"

        results.append({
            "Ticker": ticker,
            "현재가": round(price,2),
            f"{period}일 MA": round(ma,2),
            f"{period}일 1σ": round(l1,2),
            f"{period}일 2σ": round(l2,2),
            "신호": sig
        })
    return pd.DataFrame(results)

if __name__ == "__main__":
    tickers = ["SOXL","SCHD","JEPI","JEPQ","QQQ","SPLG","TMF","NVDA"]

    # — 20일 기준
    df20 = check_std_buy_signal_auto(tickers, period=20)
    header20 = "===== 20일(1개월) 기준 매수 신호 ====="
    print("\n"+header20)
    print(df20.to_string(index=False))

    # — 252일 기준
    df252 = check_std_buy_signal_auto(tickers, period=252)
    header252 = "===== 252일(1년) 기준 매수 신호 ====="
    print("\n"+header252)
    print(df252.to_string(index=False))

    # — 메시지 조합
    body = "\n".join([header20, df20.to_string(index=False),
                      "", header252, df252.to_string(index=False)])
    # 1) 텔레그램 전송
    send_telegram(body)
    # 2) 이메일 전송
    send_email("Sigma Buy Signals", body)
