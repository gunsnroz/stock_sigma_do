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
    s = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    s.login(user, pwd)
    s.sendmail(user, [to], m.as_string())
    s.quit()

def build_table(df_map, prev_price, title):
    rows = []
    for t, df in df_map.items():
        closes  = df['Close']
        ret60   = closes.pct_change(60).dropna()
        sigma60 = float(ret60.std() * 100)       # 60-day return σ%
        ma252   = float(closes.rolling(252).mean().iloc[-1])
        p1      = ma252 * (1 - sigma60/100)
        p2      = ma252 * (1 - 2 * sigma60/100)
        yest    = prev_price[t]
        if yest < p2:
            sig = "매수(2σ 이하)"
        elif yest < p1:
            sig = "매수(1σ 이하)"
        else:
            sig = "대기"
        rows.append({
            "Ticker":   t,
            "전일종가":  round(yest, 2),
            "1σ가":     round(p1,   2),
            "2σ가":     round(p2,   2),
            "신호":      sig
        })
    return title, pd.DataFrame(rows)

if __name__=="__main__":
    tickers = ["SOXL","SCHD","JEPI","JEPQ","QQQ","SPLG","TMF","NVDA"]

    # ── 전일 종가 가져오기 ──
    df0 = yf.download(tickers, period="2d", progress=False)["Close"].dropna()
    prev_price = {t: float(df0[t].iloc[-2]) for t in tickers}

    # ── 최근 1년치(365일) ──
    df1 = {t: yf.download(t, period="365d", progress=False)[["Close"]].dropna()
           for t in tickers}
    title1, tab1 = build_table(df1, prev_price, "@최근1년기준(전일종가 기준)")

    # ── 전월 동기부터 1년 ──
    today    = dt.date.today()
    prev_mon = today - dt.timedelta(days=30)
    start2   = prev_mon - dt.timedelta(days=365)
    df2 = {t: yf.download(
             t,
             start=start2.isoformat(),
             end=prev_mon.isoformat(),
             progress=False
           )[["Close"]].dropna()
           for t in tickers}
    title2, tab2 = build_table(df2, prev_price, "@전월동기→1년기준(전일종가 기준)")

    out = "\n".join([
        title1, tab1.to_string(index=False),
        "", title2, tab2.to_string(index=False)
    ])
    print(out)
    send_telegram(out)
    send_email("Sigma Buy Signals (Y-day Close Bands)", out)