#!/usr/bin/env python3
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

import os, sys, datetime as dt
import yfinance as yf
import requests
import smtplib
from email.mime.text import MIMEText
from email.utils     import formataddr

def send_telegram(html_msg):
    payload = {
        "chat_id":    os.environ['TELEGRAM_CHAT_ID'],
        "text":       f"<pre>{html_msg}</pre>",
        "parse_mode": "HTML"
    }
    requests.post(
        f"https://api.telegram.org/bot{os.environ['TELEGRAM_TOKEN']}/sendMessage",
        json=payload
    )

def send_email(subject, body):
    user, pwd, to = os.environ['EMAIL_USER'], os.environ['EMAIL_PASS'], os.environ['EMAIL_TO']
    html = f"<pre>{body}</pre>"
    msg  = MIMEText(html, _subtype='html', _charset='utf-8')
    msg['Subject'], msg['From'], msg['To'] = subject, formataddr(("Sigma Alert", user)), to
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(user, pwd)
        s.sendmail(user, [to], msg.as_string())

def main():
    # 1) 날짜 인자 처리 (YY/MM/DD), 없으면 오늘
    if len(sys.argv)>1:
        try:
            base_date = dt.datetime.strptime(sys.argv[1], "%y/%m/%d").date()
        except:
            print("날짜 형식 오류: YY/MM/DD")
            sys.exit(1)
    else:
        base_date = dt.date.today()
    nxt = base_date + dt.timedelta(1)

    # 2) 대상 티커
    tickers = ["SOXL","SCHD","JEPI","JEPQ","QQQ","SPLG","TMF","NVDA"]

    # 3) 기준일 종가
    if base_date == dt.date.today():
        df_price = yf.download(tickers, period="2d", progress=False)["Close"]
    else:
        df_price = yf.download(tickers,
                               start=base_date.isoformat(),
                               end=nxt.isoformat(),
                               progress=False)["Close"]
    price_ser = df_price.iloc[-1]

    # 4) 과거 1년치 + 전월말→1년치
    s1 = (base_date - dt.timedelta(365)).isoformat()
    full1 = {t: yf.download(t, start=s1, end=nxt.isoformat(), progress=False)["Close"].dropna()
             for t in tickers}
    pm = (base_date.replace(day=1) - dt.timedelta(1))
    s2 = (pm - dt.timedelta(365)).isoformat()
    full2 = {
      t: (yf.download(t, start=s2, end=nxt.isoformat(), progress=False)["Close"]
            .dropna().loc[:pm.isoformat()])
      for t in tickers
    }

    # 5) 출력 문자열 조립 (60일 σ / 컬럼폭 6칸 / @로 표시)
    sections = [("@ 최근1년기준", full1), ("@ 전월말→1년기준", full2)]
    lines = []
    for title, data in sections:
        lines.append(f"{title}({base_date})")
        lines.append(f"{'티커':<6}{'종가':>6}{'1σ':>6}{'2σ':>6}")
        for t in tickers:
            prev = float(price_ser[t])
            ser  = data[t].pct_change(60).dropna()
            σ    = float(ser.std()*100)
            p1, p2 = prev*(1-σ/100), prev*(1-2*σ/100)
            lines.append(f"{t:<6}{prev:6.2f}{p1:6.2f}{p2:6.2f}")
        lines.append("")  # 섹션 구분용 빈 줄

    output = "\n".join(lines)

    # 6) 출력 & 전송
    title = f"Sigma Signals ({base_date})"
    print(output)
    send_telegram(output)
    send_email(title, output)

if __name__=="__main__":
    main()
