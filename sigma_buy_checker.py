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
    rows=[]
    for t, df in df_map.items():
        closes = df['Close']
        price  = float(closes.iloc[-1])
        ma60   = float(closes.rolling(60).mean().iloc[-1])
        # σ_daily_pct: 일별 수익률 표준편차 ×100
        sigma_pct = float(closes.pct_change().dropna().std() * 100)
        p1 = ma60 * (1 - sigma_pct/100)
        p2 = ma60 * (1 - 2*sigma_pct/100)
        sig= "매수(2σ 이하)" if price < p2 else "매수(1σ 이하)" if price < p1 else "대기"
        rows.append({
            "Ticker":t, "현재가":round(price,2), "MA60":round(ma60,2),
            "σ%":round(sigma_pct,2), "1σ가":round(p1,2), "2σ가":round(p2,2), "신호":sig
        })
    return title, pd.DataFrame(rows)

if __name__=="__main__":
    tickers = ["SOXL","SCHD","JEPI","JEPQ","QQQ","SPLG","TMF","NVDA"]
    today = dt.date.today()
    prev_month = today - dt.timedelta(days=30)

    # 최근 365d
    df1 = {t:yf.download(t,period="365d",progress=False)[["Close"]].dropna() for t in tickers}
    title1, tab1 = build_table(df1, "===== 최근 1년치(365d) σ_daily 전략 =====")

    # 전월 동기부터 1년
    start2 = prev_month - dt.timedelta(days=365)
    df2 = {t:yf.download(t,start=start2.isoformat(),end=prev_month.isoformat(),progress=False)[["Close"]].dropna()
           for t in tickers}
    title2, tab2 = build_table(df2, "===== 전월 동기부터 1년 σ_daily 전략 =====")

    out = "\n".join([title1, tab1.to_string(index=False), "", title2, tab2.to_string(index=False)])
    print(out)
    send_telegram(out)
    send_email("Sigma Buy Signals (Daily Vol)", out)
