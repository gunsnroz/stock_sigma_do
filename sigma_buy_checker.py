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
        closes   = df['Close']
        # 1) 오늘 종가 (스칼라)
        price    = float(closes.iloc[-1])
        # 2) 60일 리턴 시리즈 σ₆₀%
        ret60    = closes.pct_change(60).dropna()
        sigma60  = float(ret60.std() * 100)
        # 3) 252일 단순 이동평균 (기준가)
        ma252    = float(closes.rolling(252).mean().iloc[-1])
        # 4) 가격 밴드
        p1       = ma252 * (1 - sigma60/100)
        p2       = ma252 * (1 - 2 * sigma60/100)
        # 5) 신호 판단
        if price < p2:
            sig = "매수(2σ 이하)"
        elif price < p1:
            sig = "매수(1σ 이하)"
        else:
            sig = "대기"
        rows.append({
            "Ticker": t,
            "현재가":  round(price,   2),
            "MA252":   round(ma252,   2),
            "σ₆₀%":    round(sigma60, 2),
            "1σ가":    round(p1,      2),
            "2σ가":    round(p2,      2),
            "신호":     sig
        })
    return title, pd.DataFrame(rows)

if __name__=="__main__":
    tickers  = ["SOXL","SCHD","JEPI","JEPQ","QQQ","SPLG","TMF","NVDA"]
    today    = dt.date.today()
    prev_mon = today - dt.timedelta(days=30)
    start2   = prev_mon - dt.timedelta(days=365)

    # 1) 최근 1년치 (365d)
    df1 = {
        t: yf.download(t, period="365d", progress=False)[["Close"]].dropna()
        for t in tickers
    }
    title1, tab1 = build_table(df1, "===== 최근 1년치 σ(60D-return) Bands (기준가: MA252) =====")

    # 2) 전월 동기부터 1년: 넉넉히 395일치 받아서 범위 자르기
    df2_full = {
        t: yf.download(t, period="395d", progress=False)[["Close"]].dropna()
        for t in tickers
    }
    df2 = {
        t: df.loc[start2.isoformat():prev_mon.isoformat()]
        for t, df in df2_full.items()
    }
    title2, tab2 = build_table(df2, "===== 전월 동기부터 1년 σ(60D-return) Bands (기준가: MA252) =====")

    # 출력 & 전송
    out = "\n".join([
        title1, tab1.to_string(index=False),
        "", title2, tab2.to_string(index=False)
    ])
    print(out)
    send_telegram(out)
    send_email("Sigma Buy Signals (252-day MA Bands)", out)