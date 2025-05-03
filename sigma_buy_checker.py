#!/usr/bin/env python3
"""
Calc. Period: 60D → 최근 60거래일 일별 수익률 σ를 구한 뒤,
연환산(annualized)하여 표시 (Bloomberg 방식)
"""

import os, requests, smtplib, math, datetime as dt
import yfinance as yf, pandas as pd
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
    m['Subject'], m['From'], m['To'] = subject, formataddr(("Sigma Alert", user)), to
    s = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    s.login(user, pwd)
    resp = s.sendmail(user, [to], m.as_string())
    s.quit()
    print("📧 Email send response", resp)

def compute_table(df, title):
    rows = []
    for t, sub in df.items():
        price = float(sub["Close"].iloc[-1])
        ma60  = float(sub["Close"].rolling(60).mean().iloc[-1])
        ret   = sub["Close"].pct_change().dropna()
        std60 = ret.rolling(60).std().iloc[-1] * 100
        ann60 = std60 * math.sqrt(252)
        p1    = ma60 * (1 - ann60/100)
        p2    = ma60 * (1 - 2*ann60/100)
        if price < p2:
            sig = "매수(2σ 이하)"
        elif price < p1:
            sig = "매수(1σ 이하)"
        else:
            sig = "대기"
        rows.append({
            "Ticker": t,
            "현재가":  round(price,2),
            "MA60":   round(ma60,2),
            "σ%":     round(ann60,2),
            "1σ가":   round(p1,2),
            "2σ가":   round(p2,2),
            "신호":   sig
        })
    df_out = pd.DataFrame(rows)
    return title, df_out

if __name__=="__main__":
    tickers = ["SOXL","SCHD","JEPI","JEPQ","QQQ","SPLG","TMF","NVDA"]

    # 1) 최근 365영업일(≈1년) 데이터
    df1 = {t: yf.download(t, period="365d", progress=False)[["Close"]].dropna() for t in tickers}
    title1, table1 = compute_table(df1, "===== 최근 1년치(365d) 기준 60D 연환산 σ 전략 =====")

    # 2) 전월 동기부터 1년
    today = dt.date.today()
    last_month = today - dt.timedelta(days=30)
    start_ym  = last_month - dt.timedelta(days=365)
    df2 = {}
    for t in tickers:
        df2[t] = yf.download(t, start=start_ym.isoformat(), end=last_month.isoformat(), progress=False)[["Close"]].dropna()
    title2, table2 = compute_table(df2, "===== 전월 동기부터 1년 기준 60D 연환산 σ 전략 =====")

    # 터미널 출력
    print(title1); print(table1.to_string(index=False))
    print()
    print(title2); print(table2.to_string(index=False))

    # 메시지 본문
    body = "\n".join([
        title1, table1.to_string(index=False),
        "", title2, table2.to_string(index=False)
    ])

    send_telegram(body)
    send_email("Sigma Buy Signals (1Y vs PrevMonth1Y, 60D σ)", body)
