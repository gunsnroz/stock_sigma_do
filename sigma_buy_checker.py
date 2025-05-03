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
        # 전일 종가, 오늘 종가
        prev_close = float(closes.iloc[-2])
        today_price = float(closes.iloc[-1])
        # 1) 252일 단순이동평균 (기준가)
        ma252 = float(closes.rolling(252).mean().iloc[-1])
        # 2) 252일간 일별 수익률 σ_daily%
        rets = closes.pct_change().dropna()
        sigma_pct = float(rets.std() * 100)
        # 3) 전일 종가 기준 밴드
        band1 = prev_close * (1 - sigma_pct/100)
        band2 = prev_close * (1 - 2*sigma_pct/100)
        # 4) 신호
        if today_price < band2:
            sig = "매수(2σ 이하)"
        elif today_price < band1:
            sig = "매수(1σ 이하)"
        else:
            sig = "대기"
        rows.append({
            "Ticker":   t,
            "전일종가":   round(prev_close, 2),
            "현재가":     round(today_price, 2),
            "MA252":    round(ma252,     2),
            "σ_daily%": round(sigma_pct, 2),
            "1σ가":     round(band1,     2),
            "2σ가":     round(band2,     2),
            "신호":      sig
        })
    return title, pd.DataFrame(rows)

if __name__=="__main__":
    tickers = ["SOXL","SCHD","JEPI","JEPQ","QQQ","SPLG","TMF","NVDA"]
    today    = dt.date.today()
    prev_mon = today - dt.timedelta(days=30)
    start2   = prev_mon - dt.timedelta(days=365)

    # 1) 최근 1년치
    df1 = {
        t: yf.download(t, period="365d", progress=False)[["Close"]].dropna()
        for t in tickers
    }
    title1, tab1 = build_table(df1, "===== 최근 1년치 σ_daily 가격 밴드 (전일종가 기준) =====")

    # 2) 전월 동기부터 1년 — 395일치 확보 후 슬라이스
    df2_full = {
        t: yf.download(t, period="395d", progress=False)[["Close"]].dropna()
        for t in tickers
    }
    df2 = {
        t: df.loc[start2.isoformat():prev_mon.isoformat()]
        for t, df in df2_full.items()
    }
    title2, tab2 = build_table(df2, "===== 전월 동기부터 1년 σ_daily 가격 밴드 (전일종가 기준) =====")

    out = "\n".join([
        title1, tab1.to_string(index=False),
        "", title2, tab2.to_string(index=False)
    ])
    print(out)
    send_telegram(out)
    send_email("Sigma Buy Signals (Daily-return Bands)", out)