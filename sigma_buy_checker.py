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

def send_email(subject, body):
    user, pwd, to = os.environ['EMAIL_USER'], os.environ['EMAIL_PASS'], os.environ['EMAIL_TO']
    m = MIMEText(body, _charset='utf-8')
    m['Subject'], m['From'], m['To'] = subject, formataddr(("Sigma Alert", user)), to
    s = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    s.login(user, pwd)
    s.sendmail(user, [to], m.as_string())
    s.quit()

def build_table(df_map, title):
    rows=[]
    for t, df in df_map.items():
        closes = df["Close"]
        price   = float(closes.iloc[-1])
        ma60    = float(closes.rolling(60).mean().iloc[-1])
        # **60D return-vol σ%**
        rets60 = closes.pct_change(periods=60).dropna()
        sigma60 = float(rets60.std()*100)
        p1 = ma60*(1 - sigma60/100)
        p2 = ma60*(1 - 2*sigma60/100)
        sig = "매수(2σ 이하)" if price < p2 else "매수(1σ 이하)" if price < p1 else "대기"
        rows.append({"Ticker":t,"현재가":round(price,2),"MA60":round(ma60,2),
                     "σ%":round(sigma60,2),"1σ가":round(p1,2),"2σ가":round(p2,2),"신호":sig})
    df_out = pd.DataFrame(rows)
    return title, df_out

if __name__=="__main__":
    tickers = ["SOXL","SCHD","JEPI","JEPQ","QQQ","SPLG","TMF","NVDA"]
    today = dt.date.today()
    prev_month = today - dt.timedelta(days=30)

    # 1) Recent 1Y (365d)
    df1 = {t:yf.download(t,period="365d",progress=False)[["Close"]].dropna() for t in tickers}
    title1, tab1 = build_table(df1,"===== 최근 1년치(365d) CalcPeriod:60D σ 전략 =====")

    # 2) PrevMonthSame→1Y
    start2 = prev_month - dt.timedelta(days=365)
    df2 = {t:yf.download(t,start=start2.isoformat(),end=prev_month.isoformat(),progress=False)[["Close"]].dropna()
           for t in tickers}
    title2, tab2 = build_table(df2,"===== 전월 동기부터 1년 CalcPeriod:60D σ 전략 =====")

    # 출력 & 전송
    out = "\n".join([title1,tab1.to_string(index=False),"",title2,tab2.to_string(index=False)])
    print(out)
    send_telegram(out)
    send_email("Sigma Buy Signals (60D return-vol σ)", out)
