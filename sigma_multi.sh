#!/usr/bin/env bash
#
# Multi‐ticker, multi‐window σ 계산 스크립트
# Usage: ./sigma_multi.sh [YYMMDD YYMMDD]

# 1) 기간 설정
if [ "$#" -eq 2 ]; then
  arg1=$1; yy1=${arg1:0:2}; mm1=${arg1:2:2}; dd1=${arg1:4:2}
  arg2=$2; yy2=${arg2:0:2}; mm2=${arg2:2:2}; dd2=${arg2:4:2}
  start_date="20${yy1}-${mm1}-${dd1}"
  end_date="20${yy2}-${mm2}-${dd2}"
  custom_flag=true
else
  end_date=$(date '+%Y-%m-%d')
  if [ "$(uname)" = "Darwin" ]; then
    start_date=$(date -v -400d '+%Y-%m-%d')
  else
    start_date=$(date -d '400 days ago' '+%Y-%m-%d')
  fi
  custom_flag=false
fi

# Python 으로 flag 전달
export CUSTOM_FLAG="$custom_flag"

# 2) Python 계산
python3 <<EOF
import os, warnings
warnings.filterwarnings("ignore", category=FutureWarning)

import yfinance as yf
from datetime import datetime, timedelta

# 커스텀 기간 여부
custom_flag = os.getenv('CUSTOM_FLAG','false').lower() == 'true'

# 종목 & 윈도우
tickers     = ["SOXL","TMF","SCHD","JEPI","JEPQ","QQQ","SPLG","NVDA","TQQQ"]
std_windows = [10,20,60,90,120,252]

# 날짜 범위
start_date = "${start_date}"
end_date   = "${end_date}"
date_fmt   = "%Y-%m-%d"
end_adj    = (datetime.strptime(end_date, date_fmt) + timedelta(days=1)).strftime(date_fmt)

# 1) 항상 전일 종가 사용
prev_close = {}
for t in tickers:
    hist = yf.download(t, period="2d", auto_adjust=True, progress=False)["Close"].dropna()
    if len(hist) >= 2:
        prev_close[t] = float(hist.iloc[-2])
    elif len(hist) == 1:
        prev_close[t] = float(hist.iloc[-1])
    else:
        prev_close[t] = None

# 2) 기준일 출력
base = yf.download(tickers[0], start=start_date, end=end_adj, auto_adjust=True, progress=False)["Close"].dropna()
print(f"@Base_date: {base.index[-1].strftime(date_fmt)}\n")

# 3) 결과 출력
for t in tickers:
    data = yf.download(t, start=start_date, end=end_adj, auto_adjust=True, progress=False)["Close"].dropna()
    rets = data.pct_change().dropna()
    pc   = prev_close.get(t)
    if pc is None:
        print(f"{t}: 현재 종가 조회 실패\n")
        continue

    # 표준 윈도우
    print(f"{t:>4s} {'종가':>4s} {'1σ':>6s} {'2σ':>6s} {'σ(%)':>7s}")
    for w in std_windows:
        if len(rets) < w: 
            continue
        s   = float(rets.tail(w).std())
        pct = s * 100
        p1  = pc * (1 - s)
        p2  = pc * (1 - 2*s)
        print(f"{w:4d} {pc:6.2f} {p1:6.2f} {p2:6.2f} {pct:5.2f}%")

    # 커스텀 기간
    if custom_flag:
        s   = float(rets.std())
        pct = s * 100
        p1  = pc * (1 - s)
        p2  = pc * (1 - 2*s)
        print(f"{'c':>4s} {pc:6.2f} {p1:6.2f} {p2:6.2f} {pct:5.2f}%")

    print()
