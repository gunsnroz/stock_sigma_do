#!/usr/bin/env python3
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

import os, sys, datetime as dt
<<<<<<< HEAD
import yfinance as yf, requests, smtplib
=======
import yfinance as yf
import requests, smtplib
>>>>>>> feature/sigma-multi
from email.mime.text import MIMEText
from email.utils import formataddr

def send_telegram(msg):
    payload = {
        "chat_id": os.environ['TELEGRAM_CHAT_ID'],
        "text":    msg,
        "parse_mode": "Markdown"
    }
    requests.post(f"https://api.telegram.org/bot{os.environ['TELEGRAM_TOKEN']}/sendMessage", json=payload)

def send_email(subject, body):
    user = os.environ['EMAIL_USER']
    pwd  = os.environ['EMAIL_PASS']
    to   = os.environ['EMAIL_TO']
    html = f"<pre>{body}</pre>"
    msg  = MIMEText(html, _subtype='html', _charset='utf-8')
    msg['Subject'], msg['From'], msg['To'] = subject, formataddr(("Sigma Alert", user)), to
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(user, pwd)
        s.sendmail(user, [to], msg.as_string())

def main():
    # 1) 날짜 인자 처리 (YY/MM/DD), 없으면 오늘
    if len(sys.argv) > 1:
        try:
            base_date = dt.datetime.strptime(sys.argv[1], "%y/%m/%d").date()
        except ValueError:
<<<<<<< HEAD
            print("날짜 형식 오류: YY/MM/DD 로 입력해 주세요.")
            sys.exit(1)
=======
            print("날짜 형식 오류: YY/MM/DD 로 입력해 주세요."); sys.exit(1)
>>>>>>> feature/sigma-multi
    else:
        base_date = dt.date.today()
    next_day = base_date + dt.timedelta(days=1)

<<<<<<< HEAD
    # 2) 티커와 윈도우 리스트
=======
    # 티커 & 윈도우
>>>>>>> feature/sigma-multi
    tickers = ["SOXL","TMF","SCHD","JEPI","JEPQ","QQQ","SPLG","NVDA"]
    windows = [10,20,60,90,120,252]

<<<<<<< HEAD
    # 3) 과거 260거래일치 종가 시리즈(각 티커별) 한 방에 받기
    full = {
        t: yf.download(t, period="260d", progress=False)["Close"]
             .dropna()
        for t in tickers
    }

    # 4) 결과 문자열 만들기
    out_lines = [f"📌 기준일: {base_date}"]
    header = f"{'티커':<6}{'종가':>8}{'1σ':>8}{'2σ':>8}{'σ(%)':>8}"
    out_lines.append("")        # 빈 줄
    out_lines.append(header)
    out_lines.append("-"*len(header))

    out_lines.append("")
    for t in tickers:
        ser   = full[t]
        price = float(ser.iloc[-1])
        # 각 윈도우 별 계산
        for w in windows:
            ret   = ser.pct_change().dropna().tail(w)
            sigma = float(ret.std() * 100)
            p1    = price * (1 - sigma/100)
            p2    = price * (1 - 2*sigma/100)
            out_lines.append(f"{t:<6}{price:8.2f}{p1:8.2f}{p2:8.2f}{sigma:8.2f}")
            # 티커 한 번만 쓰고, 윈도우는 /로 붙여 쓰고 싶으시면 아래처럼 바꿀 수도 있습니다.
            # windows_str = "/".join(map(str, windows))
            # out_lines.append(f"{windows_str:>6}{price:8.2f}{p1:8.2f}{p2:8.2f}{sigma:8.2f}")

    output = "\n".join(out_lines)

    # 5) 출력 및 전송
=======
    # 기준일 종가
    if base_date == dt.date.today():
        df_price = yf.download(tickers, period="2d", progress=False)["Close"]
    else:
        df_price = yf.download(tickers, start=base_date.isoformat(), end=next_day.isoformat(), progress=False)["Close"]
    price_ser = df_price.iloc[-1]

    # 과거 1년치 종가
    start_1y = (base_date - dt.timedelta(days=365)).isoformat()
    full = {
        t: yf.download(t, start=start_1y, end=next_day.isoformat(), progress=False)["Close"].dropna()
        for t in tickers
    }

    # 출력 조립
    out = [f"📌 기준일: {base_date}"]
    for t in tickers:
        price = float(price_ser[t])
        out.append(f"\n{t:<6}{'종가':>8}{'1σ':>8}{'2σ':>8}{'σ(%)':>8}")
        for w in windows:
            ser   = full[t].pct_change().dropna().tail(w)
            sigma = float(ser.std() * 100)
            p1    = price * (1 - sigma/100)
            p2    = price * (1 - 2*sigma/100)
            out.append(f"{w:<6}{price:8.2f}{p1:8.2f}{p2:8.2f}{sigma:8.2f}")
    output = "\n".join(out)

    # 출력·전송
>>>>>>> feature/sigma-multi
    title = f"Sigma Signals ({base_date})"
    print(output)
    send_telegram(output)
    send_email(title, output)

if __name__ == "__main__":
    main()
