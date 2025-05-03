#!/usr/bin/env python
import os, requests, smtplib, yfinance as yf, pandas as pd
from email.mime.text import MIMEText
from email.utils import formataddr
import math

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
    resp = s.sendmail(user, [to], m.as_string())
    s.quit()
    print("📧 Email send response", resp)

def check_std_buy_signal_returns(tickers, period=20, k1=1, k2=2):
    rows = []
    for t in tickers:
        df = yf.download(t, period=f"{period*3}d", progress=False)[["Close"]].dropna()
        price   = float(df["Close"].iloc[-1])
        ma      = float(df["Close"].rolling(window=period).mean().iloc[-1])

        # 일별 returns
        ret = df["Close"].pct_change().dropna()
        # 1) returns-based daily σ% (20일)
        std20_pct   = float(ret.rolling(window=period).std().iloc[-1] * 100)
        # 2) returns-based annualized σ% (20일)
        ann20_pct   = std20_pct * math.sqrt(252)
        # 3) returns-based annualized σ% for 60일 (Bloomberg 스타일)
        std60_pct   = float(ret.rolling(window=60).std().iloc[-1] * 100)
        ann60_pct   = std60_pct * math.sqrt(252)

        # price deviation %
        dev_pct = (price / ma - 1) * 100 
        # 1σ/2σ price levels
        price_1σ = ma * (1 - k1 * std20_pct/100)
        price_2σ = ma * (1 - k2 * std20_pct/100)

        if dev_pct < -k2 * std20_pct:
            sig = f"매수(2σ 이하)"
        elif dev_pct < -k1 * std20_pct:
            sig = f"매수(1σ 이하)"
        else:
            sig = "대기"

        rows.append({
            "Ticker":        t,
            "현재가":         round(price,2),
            f"{period}일 MA":  round(ma,2),
            "20일 σ%":       round(std20_pct,2),
            "20a σ%":        round(ann20_pct,2),
            "60a σ%":        round(ann60_pct,2),  # ← 이게 Bloomberg 의 7.05% 같은 값
            "1σ 가격":        round(price_1σ,2),
            "2σ 가격":        round(price_2σ,2),
            "신호":          sig
        })
    return pd.DataFrame(rows)

if __name__=="__main__":
    tickers = ["SOXL","SCHD","JEPI","JEPQ","QQQ","SPLG","TMF","NVDA"]

    df20 = check_std_buy_signal_returns(tickers, period=20)
    print("===== 20일 Returns σ 전략 =====")
    print(df20.to_string(index=False))

    # 252일 전략 (유사하게 연환산 σ%)
    df252 = check_std_buy_signal_returns(tickers, period=252)
    print("===== 252일 Returns σ 전략 =====")
    print(df252.to_string(index=False))

    body = "\n".join([
        "===== 20일 Returns σ 전략 =====", df20.to_string(index=False),
        "", "===== 252일 Returns σ 전략 =====", df252.to_string(index=False)
    ])
    send_telegram(body)
    send_email("Sigma Buy Signals (returns σ)", body)
