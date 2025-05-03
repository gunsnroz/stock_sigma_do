#!/usr/bin/env python3
import os, requests, smtplib, math
import yfinance as yf, pandas as pd
from email.mime.text import MIMEText
from email.utils import formataddr

#─────────────────────────────────────────────────────────
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
#─────────────────────────────────────────────────────────

def check_60d_sigma(tickers, k1=1, k2=2):
    rows = []
    for t in tickers:
        df = yf.download(t, period="300d", progress=False)[["Close"]].dropna()
        price = float(df["Close"].iloc[-1])
        ma60  = float(df["Close"].rolling(60).mean().iloc[-1])

        # 60d daily returns σ% → annualized σ%
        ret     = df["Close"].pct_change().dropna()
        std60   = ret.rolling(60).std().iloc[-1] * 100
        ann60   = std60 * math.sqrt(252)

        # 1σ/2σ 매수가격
        p1 = ma60 * (1 - ann60/100 * k1)
        p2 = ma60 * (1 - ann60/100 * k2)

        # 신호 판단 (60d ann σ 기준)
        if price < p2:
            sig = "매수(2σ 이하)"
        elif price < p1:
            sig = "매수(1σ 이하)"
        else:
            sig = "대기"

        rows.append({
            "Ticker": t,
            "현재가": round(price,2),
            "기준가": round(ma60,2),
            "1σ가":  round(p1,2),
            "2σ가":  round(p2,2),
            "신호":   sig
        })
    return pd.DataFrame(rows)

if __name__=="__main__":
    tickers = ["SOXL","SCHD","JEPI","JEPQ","QQQ","SPLG","TMF","NVDA"]

    df = check_60d_sigma(tickers)
    txt = df.to_string(index=False)
    print("===== 60거래일 연환산 σ 전략 =====")
    print(txt)

    # 전송
    send_telegram(txt)
    send_email("Sigma Buy Signals (60d ann σ)", txt)
