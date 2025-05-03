#!/usr/bin/env python3
"""
60D Annualized σ (Bloomberg 방식) – 거래일 기준 정확히 60거래일

1) Recent 252 trading days  (≈1년치)
2) PrevMonthSame→252td    (전월 동기부터 252거래일)

Calc. Period: 60 trading days → 일별 수익률 σ → √252 연환산 σ(%)
"""

import os, requests, smtplib, math, datetime as dt
import yfinance as yf, pandas as pd
from email.mime.text import MIMEText
from email.utils import formataddr

def get_trading_close(ticker, start, end):
    # start/end를 거래일 기준으로 지정해서 정확하게 데이터를 가져옵니다.
    df = yf.download(ticker, start=start, end=end, progress=False)[["Close"]]
    df = df.dropna()
    return df

def calc_ann_sigma(closes, window=60):
    rets = closes.pct_change().dropna()
    # 정확한 'window' 거래일 σ
    sigma_daily = rets.rolling(window=window).std().iloc[-1]
    return float(sigma_daily * math.sqrt(252) * 100)

def build_table(df_map):
    rows = []
    for t, df in df_map.items():
        closes = df["Close"]
        price = float(closes.iloc[-1])
        # 60 trading days moving average
        ma60  = float(closes.rolling(window=60).mean().iloc[-1])
        sigma = calc_ann_sigma(closes, window=60)
        p1    = ma60 * (1 - sigma/100)
        p2    = ma60 * (1 - 2*sigma/100)
        sig   = "매수(2σ 이하)" if price < p2 else "매수(1σ 이하)" if price < p1 else "대기"
        rows.append({
            "Ticker": t,
            "현재가": round(price,2),
            "MA60":  round(ma60,2),
            "σ%":    round(sigma,2),
            "1σ가":  round(p1,2),
            "2σ가":  round(p2,2),
            "신호":  sig
        })
    return pd.DataFrame(rows)

if __name__=="__main__":
    tickers = ["SOXL","SCHD","JEPI","JEPQ","QQQ","SPLG","TMF","NVDA"]
    today = dt.date.today()

    # 1) Recent 252 trading days (약 1년치)
    start1 = today - dt.timedelta(days=365)
    df1 = {t: get_trading_close(t, start=start1.isoformat(), end=today.isoformat()) for t in tickers}
    table1 = build_table(df1)

    # 2) PrevMonthSame → 252 trading days
    prev_month_day = today - dt.timedelta(days=30)
    start2 = prev_month_day - dt.timedelta(days=365)
    df2 = {t: get_trading_close(t, start=start2.isoformat(), end=prev_month_day.isoformat()) for t in tickers}
    table2 = build_table(df2)

    # 출력
    title1 = "===== 최근 1년치(252td) 기준 60t 연환산 σ 전략 ====="
    title2 = "===== 전월 동기부터 1년(252td) 기준 60t 연환산 σ 전략 ====="
    print(title1); print(table1.to_string(index=False))
    print(); print(title2); print(table2.to_string(index=False))

    # 메시지 본문
    body = "\n".join([title1, table1.to_string(index=False), "", title2, table2.to_string(index=False)])
    # Telegram
    resp = requests.post(
        f"https://api.telegram.org/bot{os.environ['TELEGRAM_TOKEN']}/sendMessage",
        json={"chat_id": os.environ['TELEGRAM_CHAT_ID'], "text": body}
    )
    print("Telegram status:", resp.status_code)
    # Email
    msg = MIMEText(body, _charset='utf-8')
    msg['Subject'] = "Sigma Signals – 60td Annualized Vol"
    msg['From']    = formataddr(("Sigma Alert", os.environ['EMAIL_USER']))
    msg['To']      = os.environ['EMAIL_TO']
    s = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    s.login(os.environ['EMAIL_USER'], os.environ['EMAIL_PASS'])
    mail_resp = s.sendmail(os.environ['EMAIL_USER'], [os.environ['EMAIL_TO']], msg.as_string())
    s.quit()
    print("Email sent:", mail_resp)
