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

def build_table(df_map, today_price, yest_close, title):
    rows = []
    for t, df in df_map.items():
        prev_close = yest_close[t]
        tp         = today_price[t]
        sigma_pct  = float(df['Close'].pct_change().dropna().std() * 100)
        band1 = prev_close * (1 - sigma_pct/100)
        band2 = prev_close * (1 - 2*sigma_pct/100)
        if   tp < band2: sig = "매수(2σ 이하)"
        elif tp < band1: sig = "매수(1σ 이하)"
        else:            sig = "대기"
        rows.append({
            "Ticker":   t,
            "전일종가":   round(prev_close, 2),
            "1σ":       round(band1,     2),
            "2σ":       round(band2,     2),
            "신호":      sig
        })
    return title, pd.DataFrame(rows)

if __name__=="__main__":
    tickers  = ["SOXL","SCHD","JEPI","JEPQ","QQQ","SPLG","TMF","NVDA"]
    today    = dt.date.today()
    prev_mon = today - dt.timedelta(days=30)
    start2   = prev_mon - dt.timedelta(days=365)

    # 1) fetch today’s last price and yesterday’s close
    df_today = yf.download(tickers, period="1d", progress=False)["Close"].iloc[-1]
    df2d     = yf.download(tickers, period="2d", progress=False)["Close"]
    today_price = {}
    yest_close  = {}
    for t in tickers:
        tp = yf.Ticker(t).fast_info.get("last_price") or float(df_today[t])
        today_price[t] = float(tp)
        yest_close[t]  = float(df2d[t].iloc[-2])   # yesterday’s close

    # 2) build @최근1년기준(전일종가 기준)
    df1 = {
        t: yf.download(t, period="365d", progress=False)[["Close"]].dropna()
        for t in tickers
    }
    title1, tab1 = build_table(df1, today_price, yest_close, "@최근1년기준(전일종가 기준)")

    # 3) build @최근1년기준(직전월, 전일종가 기준)
    df_full = {
        t: yf.download(t, period="395d", progress=False)[["Close"]].dropna()
        for t in tickers
    }
    df2 = {
        t: df.loc[start2.isoformat():prev_mon.isoformat()]
        for t, df in df_full.items()
    }
    title2, tab2 = build_table(df2, today_price, yest_close, "@최근1년기준(직전월, 전일종가 기준)")

    # 4) output & notify
    out = "\n".join([
        title1, tab1.to_string(index=False),
        "", title2, tab2.to_string(index=False)
    ])
    print(out)
    send_telegram(out)
    send_email("Sigma Buy Signals (한방버전)", out)