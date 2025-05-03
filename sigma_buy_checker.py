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

def build_table(df_map, title):
    rows = []
    for t, df in df_map.items():
        closes = df['Close']
        # 1) 오늘 수익률(%)
        rets       = closes.pct_change().dropna()
        today_ret  = float(rets.iloc[-1] * 100)
        # 2) daily σ%
        sigma_pct  = float(rets.std() * 100)
        # 3) MA60 (차트 참고용)
        ma60       = float(closes.rolling(60).mean().iloc[-1])
        # 4) 시그널(등락률 기준)
        if today_ret <= -2*sigma_pct:
            sig = "매수(2σ 이하)"
        elif today_ret <= -1*sigma_pct:
            sig = "매수(1σ 이하)"
        else:
            sig = "대기"
        rows.append({
            "Ticker":t,
            "현재가": round(closes.iloc[-1],2),
            "MA60":   round(ma60,2),
            "오늘등락%": round(today_ret,2),
            "σ_daily%": round(sigma_pct,2),
            "신호":    sig
        })
    return title, pd.DataFrame(rows)

if __name__=="__main__":
    tickers = ["SOXL","SCHD","JEPI","JEPQ","QQQ","SPLG","TMF","NVDA"]
    today    = dt.date.today()
    prev_mon = today - dt.timedelta(days=30)

    # 최근 1년(365d)
    df1 = {t: yf.download(t, period="365d", progress=False)[["Close"]].dropna()
           for t in tickers}
    title1, tab1 = build_table(df1, "===== 최근 1년치 σ_daily 등락률 전략 =====")

    # 전월 동기부터 1년
    start2 = prev_mon - dt.timedelta(days=365)
    df2 = {t: yf.download(t, start=start2.isoformat(), end=prev_mon.isoformat(), progress=False)[["Close"]].dropna()
           for t in tickers}
    title2, tab2 = build_table(df2, "===== 전월 동기부터 1년 σ_daily 등락률 전략 =====")

    out = "\n".join([
        title1, tab1.to_string(index=False),
        "", title2, tab2.to_string(index=False)
    ])
    print(out)
    send_telegram(out)
    send_email("Sigma Buy Signals (Daily Return-Vol Strategy)", out)
