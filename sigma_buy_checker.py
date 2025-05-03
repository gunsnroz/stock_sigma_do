#!/usr/bin/env python3
import os, requests, smtplib, datetime as dt
import yfinance as yf, pandas as pd
from email.mime.text import MIMEText
from email.utils import formataddr

def send_telegram(msg):
    requests.post(
        f"https://api.telegram.org/bot{os.environ['TELEGRAM_TOKEN']}/sendMessage",
        json={"chat_id": os.environ['TELEGRAM_CHAT_ID'], "text": msg}
    )

def send_email(subj, body):
    user, pwd, to = os.environ['EMAIL_USER'], os.environ['EMAIL_PASS'], os.environ['EMAIL_TO']
    m = MIMEText(body, _charset='utf-8')
    m['Subject'], m['From'], m['To'] = subj, formataddr(("Sigma Alert", user)), to
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(user, pwd)
        s.sendmail(user, [to], m.as_string())

def build_table(df_map, title):
    rows = []
    for t, df in df_map.items():
        closes     = df['Close']
        prev_close = float(closes.iloc[-2])
        today_price= float(closes.iloc[-1])
        sigma_pct  = float(closes.pct_change().dropna().std() * 100)
        band1      = prev_close * (1 - sigma_pct/100)
        band2      = prev_close * (1 - 2*sigma_pct/100)
        if   today_price < band2: sig = "매수(2σ 이하)"
        elif today_price < band1: sig = "매수(1σ 이하)"
        else:                     sig = "대기"
        rows.append({
            "Ticker":    t,
            "현재가":      round(today_price,  2),
            "전일종가":    round(prev_close,    2),
            "1σ":        round(band1,         2),
            "2σ":        round(band2,         2),
            "신호":       sig
        })
    return title, pd.DataFrame(rows)

if __name__=="__main__":
    tickers  = ["SOXL","SCHD","JEPI","JEPQ","QQQ","SPLG","TMF","NVDA"]
    today    = dt.date.today()
    prev_mon = today - dt.timedelta(days=30)
    start2   = prev_mon - dt.timedelta(days=365)

    # 최근 1년치 (365d)
    df1 = {
        t: yf.download(t, period="365d", progress=False)[["Close"]].dropna()
        for t in tickers
    }
    title1, tab1 = build_table(df1, "@최근1년기준(전일종가 기준)")

    # 전월 동기부터 1년 — 395일 확보 후 범위 자르기
    df2_full = {
        t: yf.download(t, period="395d", progress=False)[["Close"]].dropna()
        for t in tickers
    }
    df2 = {
        t: df.loc[start2.isoformat():prev_mon.isoformat()]
        for t, df in df2_full.items()
    }
    title2, tab2 = build_table(df2, "@최근1년기준(직전월, 전일종가 기준)")

    out = "\n".join([
        title1, tab1.to_string(index=False),
        "", title2, tab2.to_string(index=False)
    ])
    print(out)
    send_telegram(out)
    send_email("Sigma Buy Signals (Simplified)", out)