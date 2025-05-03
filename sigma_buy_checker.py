#!/usr/bin/env python
import os, requests, smtplib, yfinance as yf, pandas as pd
from email.mime.text import MIMEText
from email.utils import formataddr

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
    m['Subject'] = subject
    m['From']    = formataddr(("Sigma Alert", user))
    m['To']      = to
    s = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    s.login(user, pwd)
    resp = s.sendmail(user, [to], m.as_string())
    s.quit()
    print("📧 Email send response", resp)

def check_std_buy_signal_returns(tickers, period=20, k1=1, k2=2):
    rows = []
    for t in tickers:
        df = yf.download(t, period=f"{period*3}d", progress=False)[["Close"]].dropna()
        price   = float(df["Close"].iloc[-1])
        ma      = float(df["Close"].rolling(window=period).mean().iloc[-1])
        # 수익률 기반 σ%
        ret     = df["Close"].pct_change().dropna()
        std_pct = float(ret.rolling(window=period).std().iloc[-1] * 100)
        # 가격 MA 대비 dev_pct %
        dev_pct = (price / ma - 1) * 100

        if dev_pct < -k2 * std_pct:
            sig = f"매수(2σ 이하, {std_pct:.2f}%)"
        elif dev_pct < -k1 * std_pct:
            sig = f"매수(1σ 이하, {std_pct:.2f}%)"
        else:
            sig = "대기"

        rows.append({
            "Ticker":       t,
            "현재가":        round(price,2),
            f"{period}일 MA": round(ma,2),
            f"{period}σ%":   round(std_pct,2),
            "편차%":         round(dev_pct,2),
            "신호":         sig
        })
    return pd.DataFrame(rows)

if __name__=="__main__":
    tickers = ["SOXL","SCHD","JEPI","JEPQ","QQQ","SPLG","TMF","NVDA"]

    # 20일(1개월) 기준 returns-based 시그마
    df20 = check_std_buy_signal_returns(tickers, period=20)
    header20 = "===== 20일(1개월) Returns σ 전략 ====="
    print(header20)
    print(df20.to_string(index=False))

    # 252일(1년) 기준 returns-based 시그마
    df252 = check_std_buy_signal_returns(tickers, period=252)
    header252 = "===== 252일(1년) Returns σ 전략 ====="
    print(header252)
    print(df252.to_string(index=False))

    # 메시지 본문 조합
    body = "\n".join([
        header20, df20.to_string(index=False),
        "", header252, df252.to_string(index=False)
    ])

    send_telegram(body)
    send_email("Sigma Buy Signals (returns σ)", body)
