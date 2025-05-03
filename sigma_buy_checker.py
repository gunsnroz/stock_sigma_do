#!/usr/bin/env python3
import os, requests, smtplib, datetime as dt, math
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

def calc_volatility(df):
    # 전체 기간 일별 수익률 → 연환산 σ%
    rets = df['Close'].pct_change().dropna()
    return float(rets.std() * math.sqrt(252) * 100)

def build_table(df_map, title):
    rows = []
    for t, df in df_map.items():
        closes = df['Close']
        price  = float(closes.iloc[-1])
        ma60   = float(closes.rolling(60).mean().iloc[-1])
        sigma  = calc_volatility(df)
        p1     = ma60 * (1 - sigma/100)
        p2     = ma60 * (1 - 2*sigma/100)
        sig    = "매수(2σ 이하)" if price < p2 else "매수(1σ 이하)" if price < p1 else "대기"
        rows.append({
            "Ticker": t,
            "현재가": round(price,2),
            "MA60": round(ma60,2),
            "σ%": round(sigma,2),
            "1σ가": round(p1,2),
            "2σ가": round(p2,2),
            "신호": sig
        })
    return title, pd.DataFrame(rows)

if __name__=="__main__":
    tickers = ["SOXL","SCHD","JEPI","JEPQ","QQQ","SPLG","TMF","NVDA"]
    today = dt.date.today()
    prev_month = today - dt.timedelta(days=30)

    # 1) 최근 1년치 (365d)
    df1 = {t: yf.download(t, period="365d", progress=False)[["Close"]].dropna() for t in tickers}
    title1, tab1 = build_table(df1, "===== 최근 1년치(365d) σ 전략 =====")

    # 2) 전월 동기부터 1년
    start2 = prev_month - dt.timedelta(days=365)
    df2 = {t: yf.download(t, start=start2.isoformat(), end=prev_month.isoformat(), progress=False)[["Close"]].dropna()
           for t in tickers}
    title2, tab2 = build_table(df2, "===== 전월 동기부터 1년 σ 전략 =====")

    # 결과
    out = "\n".join([
        title1, tab1.to_string(index=False),
        "", title2, tab2.to_string(index=False)
    ])
    print(out)
    send_telegram(out)
    send_email("Sigma Buy Signals (Annualized Daily Vol)", out)
