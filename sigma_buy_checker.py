#!/usr/bin/env python3
import yfinance as yf
import pandas as pd
import requests
import smtplib
from email.mime.text import MIMEText

# ── 사용자 설정 ────────────────────────────────────
# Telegram
TELEGRAM_TOKEN   = "7335635442:AAHPdFASBJKFRkaWrOyQ-08E_iFzIBBk8I8"
TELEGRAM_CHAT_ID = 7585700210

# Email
EMAIL_USER = "kongzi@caia.kr"
EMAIL_PASS = "uazl jldc jupl hndw"
EMAIL_TO   = "kongzi@me.com"

# ── 알림 함수 ──────────────────────────────────────
def send_telegram(msg: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": msg}
    requests.post(url, data=data)

def send_email(subject: str, msg: str):
    mime = MIMEText(msg)
    mime["Subject"] = subject
    mime["From"]    = EMAIL_USER
    mime["To"]      = EMAIL_TO
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(EMAIL_USER, EMAIL_PASS)
        s.send_message(mime)

# ── 표준편차 매수 판단 함수 ─────────────────────────
def check_std_buy_signal_auto(tickers, period=20, k1=1, k2=2):
    results = []
    for ticker in tickers:
        df = yf.download(ticker, period="60d", progress=False)[["Close"]].copy()
        df["MA"]  = df["Close"].rolling(window=period).mean()
        df["STD"] = df["Close"].rolling(window=period).std()
        df = df.dropna()
        if df.empty:
            continue

        last = df.iloc[-1]
        price = float(last["Close"])
        ma    = float(last["MA"])
        std   = float(last["STD"])
        l1    = ma - k1 * std
        l2    = ma - k2 * std

        if price < l2:
            sig = "매수(2σ 이하)"
        elif price < l1:
            sig = "매수(1σ 이하)"
        else:
            sig = "대기"

        results.append({
            "Ticker": ticker,
            "현재가": round(price,2),
            "20일평균": round(ma,2),
            "1σ하단": round(l1,2),
            "2σ하단": round(l2,2),
            "신호": sig
        })
    return pd.DataFrame(results)

# ── 메인 실행부 ─────────────────────────────────────
if __name__ == "__main__":
    tickers = ["SOXL","SCHD","JEPI","JEPQ","QQQ","SPLG","TMF","NVDA"]
    df = check_std_buy_signal_auto(tickers)

    # 1) 터미널 출력
    print(df.to_string(index=False))

    # 2) Telegram 알림
    send_telegram(df.to_string(index=False))

    # 3) Email 알림
    send_email("표준편차 매수 신호 알림", df.to_string(index=False))
