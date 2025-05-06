#!/usr/bin/env bash
#
# Multi‐ticker, multi‐window σ 계산 스크립트
#
# Usage:
#   ./sigma_multi.sh
#   ./sigma_multi.sh YYMMDD YYMMDD   (예: 250102 250503)

# 1) 기간 설정
if [ "$#" -eq 2 ]; then
  arg1=$1
  yy1=${arg1:0:2}; mm1=${arg1:2:2}; dd1=${arg1:4:2}
  arg2=$2
  yy2=${arg2:0:2}; mm2=${arg2:2:2}; dd2=${arg2:4:2}
  start_date="20${yy1}-${mm1}-${dd1}"
  end_date="20${yy2}-${mm2}-${dd2}"
else
  end_date=$(date '+%Y-%m-%d')
  start_date=$(date -v -400d '+%Y-%m-%d')
fi

# 2) Python 계산 블록
python3 <<PYCODE
import warnings; warnings.filterwarnings("ignore", category=FutureWarning)
import yfinance as yf
from datetime import datetime, timedelta

tickers     = ["SOXL","TMF","SCHD","JEPI","JEPQ","QQQ","SPLG","NVDA"]
all_windows = [10,20,60,90,120,252]

start_date = "$start_date"
end_date   = "$end_date"
end_adj    = (datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")

# 2.1 현재 종가
prev_close = {}
for t in tickers:
    hist = yf.download(t, period="2d", auto_adjust=True, progress=False)["Close"].dropna()
    prev_close[t] = float(hist.iloc[-1]) if not hist.empty else None

# 2.2 기준일 출력
base = yf.download(tickers[0], start=start_date, end=end_adj, auto_adjust=True, progress=False)["Close"].dropna()
print(f"@Base_date: {base.index[-1].strftime('%Y-%m-%d')}\n")

# 2.3 윈도우별 σ·1σ·2σ 계산·출력
for t in tickers:
    data = yf.download(t, start=start_date, end=end_adj, auto_adjust=True, progress=False)["Close"].dropna()
    rets = data.pct_change().dropna()
    pc   = prev_close.get(t)
    if pc is None:
        print(f"{t}: 현재 종가 조회 실패\n")
        continue

    windows = [w for w in all_windows if len(rets) >= w]
    if not windows:
        print(f"{t}: 지정 기간({start_date}~{end_date})에 거래일 부족\n")
        continue

    print(f"{t:<5s} {'현재가':>8s} {'1σ가':>8s} {'2σ가':>8s} {'σ(%)':>8s}")
    for w in windows:
        s   = float(rets.tail(w).std())
        pct = s * 100
        p1  = pc * (1 - s)
        p2  = pc * (1 - 2*s)
        print(f"{w:6d} {pc:8.2f} {p1:8.2f} {p2:8.2f} {pct:8.2f}%")
    print()
PYCODE
