#!/usr/bin/env python3
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

import os, sys
import datetime as dt
import yfinance as yf
import requests
import smtplib
from email.mime.text import MIMEText
from email.utils     import formataddr

def send_telegram(msg):
    payload = {
        "chat_id": os.environ['TELEGRAM_CHAT_ID'],
        "text":    f"```{msg}```",
        "parse_mode": "Markdown"
    }
    requests.post(
        f"https://api.telegram.org/bot{os.environ['TELEGRAM_TOKEN']}/sendMessage",
        json=payload
    )

def send_email(subject, body):
    user = os.environ['EMAIL_USER']
    pwd  = os.environ['EMAIL_PASS']
    to   = os.environ['EMAIL_TO']
    html = f"<pre>{body}</pre>"
    msg  = MIMEText(html, _subtype='html', _charset='utf-8')
    msg['Subject'] = subject
    msg['From']    = formataddr(("Sigma Alert", user))
    msg['To']      = to
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(user, pwd)
        s.sendmail(user, [to], msg.as_string())

def main():
    # 1) 날짜 인자 처리 (YY/MM/DD), 없으면 오늘
    if len(sys.argv) > 1:
        try:
            base_date = dt.datetime.strptime(sys.argv[1], "%y/%m/%d").date()
        except ValueError:
            print("날짜 형식 오류: YY/MM/DD 로 입력해 주세요.")
            sys.exit(1)
    else:
        base_date = dt.date.today()
    next_day = base_date + dt.timedelta(days=1)

    # 2) 티커와 윈도우 리스트
    tickers = ["SOXL","TMF","SCHD","JEPI","JEPQ","QQQ","SPLG","NVDA"]
    windows = [10, 20, 60, 90, 252]

    # 3) 기준일 종가 가져오기
    if base_date == dt.date.today():
        df_price  = yf.download(tickers, period="2d", progress=False)["Close"]
    else:
        df_price  = yf.download(
            tickers,
            start=base_date.isoformat(),
            end=next_day.isoformat(),
            progress=False
        )["Close"]
    price_ser = df_price.iloc[-1]

    # 4) 과거 1년치 데이터 준비
    start_1y = (base_date - dt.timedelta(days=365)).isoformat()
    full = {
        t: yf.download(
             t,
             start=start_1y,
             end=next_day.isoformat(),
             progress=False
           )["Close"].dropna()
        for t in tickers
    }

    # 5) 결과 문자열 만들기 (맨 앞에 기준일 📌 이모지 포함)
    out_lines = [f"📌 기준일: {base_date}"]
    for t in tickers:
        price = float(price_ser[t])
        # 헤더 및 구분선
        header = f"{t:<6}{'종가':>8}{'1σ':>8}{'2σ':>8}{'σ(%)':>8}"
        out_lines.append("")                # 빈 줄
        out_lines.append(header)
        out_lines.append("-" * len(header)) # 구분선
        # 윈도우별 행
        for w in windows:
            ser   = full[t].pct_change().dropna().tail(w)
            sigma = float(ser.std() * 100)
            p1    = price * (1 - sigma/100)
            p2    = price * (1 - 2*sigma/100)
            out_lines.append(f"{w:<6}{price:8.2f}{p1:8.2f}{p2:8.2f}{sigma:8.2f}")

    output = "\n".join(out_lines)

    # 6) 출력 및 전송
    title = f"Sigma Signals ({base_date})"
    print(output)
    send_telegram(output)
    send_email(title, output)

if __name__ == "__main__":
    main()
