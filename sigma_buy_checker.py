#!/usr/bin/env python3
import os, sys, datetime as dt
import yfinance as yf, pandas as pd, requests, smtplib
from email.mime.text import MIMEText
from email.utils import formataddr

def send_telegram(msg):
    payload = {
        "chat_id": os.environ['TELEGRAM_CHAT_ID'],
        "text": f"```{msg}```",
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

def build_rows(dfs, price_ser):
    rows = []
    for t, df in dfs.items():
        prev      = float(price_ser[t])
        # 60거래일 수익률 기준 σ 계산
        sigma_pct = float(df['Close'].pct_change(60).dropna().std() * 100)
        p1        = prev * (1 - sigma_pct/100)
        p2        = prev * (1 - 2*sigma_pct/100)
        rows.append((t, prev, p1, p2))
    return rows

def format_table(title, rows):
    lines = [ title, f"{'티커':<6}{'종가':>8}{'1σ':>8}{'2σ':>8}" ]
    for t, prev, p1, p2 in rows:
        lines.append(f"{t:<6}{prev:>8.2f}{p1:>8.2f}{p2:>8.2f}")
    return "\n".join(lines)

if __name__ == "__main__":
    # 1) 날짜 인자 처리 (YY/MM/DD), 없으면 오늘
    if len(sys.argv) > 1:
        try:
            base_date = dt.datetime.strptime(sys.argv[1], "%y/%m/%d").date()
        except ValueError:
            print("날짜 형식 오류: YY/MM/DD 로 입력해 주세요.")
            sys.exit(1)
    else:
        base_date = dt.date.today()
    next_day   = base_date + dt.timedelta(days=1)

    tickers    = ["SOXL","SCHD","JEPI","JEPQ","QQQ","SPLG","TMF","NVDA"]

    # 2) 기준일 종가 가져오기
    if base_date == dt.date.today():
        df_price  = yf.download(tickers, period="2d", progress=False)["Close"]
        price_ser = df_price.iloc[-1]
    else:
        df_price  = yf.download(
            tickers,
            start=base_date.isoformat(),
            end=next_day.isoformat(),
            progress=False
        )["Close"]
        price_ser = df_price.iloc[-1]

    # 3) 최근 1년 기준
    start_1y = base_date - dt.timedelta(days=365)
    dfs1 = {
        t: yf.download(t,
                       start=start_1y.isoformat(),
                       end=next_day.isoformat(),
                       progress=False)[["Close"]].dropna()
        for t in tickers
    }
    rows1 = build_rows(dfs1, price_ser)
    txt1  = format_table(f"📍최근1년기준({base_date})", rows1)

    # 4) 전월말→1년 기준
    prev_month = base_date.replace(day=1) - dt.timedelta(days=1)
    start2     = prev_month - dt.timedelta(days=365)
    dfs2 = {
        t: (
            yf.download(t,
                        start=start2.isoformat(),
                        end=next_day.isoformat(),
                        progress=False)[["Close"]].dropna()
        ).loc[:prev_month.isoformat()]
        for t in tickers
    }
    rows2 = build_rows(dfs2, price_ser)
    txt2  = format_table(f"📍전월말→1년기준({base_date})", rows2)

    # 5) 출력 & 전송
    out = txt1 + "\n\n" + txt2
    print(out)
    send_telegram(out)
    send_email(f"Sigma Signals ({base_date})", out)
