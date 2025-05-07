#!/usr/bin/env bash
#
# Multi‐ticker, multi‐window σ 계산 스크립트
# Usage: ./sigma_multi.sh [YYMMDD YYMMDD]

# 1) 기간 설정
if [ "$#" -eq 2 ]; then
  yy1=${1:0:2}; mm1=${1:2:2}; dd1=${1:4:2}
  yy2=${2:0:2}; mm2=${2:2:2}; dd2=${2:4:2}
  START_DATE="20${yy1}-${mm1}-${dd1}"
  END_DATE="20${yy2}-${mm2}-${dd2}"
  CUSTOM_FLAG=true
else
  END_DATE=$(date '+%Y-%m-%d')
  if [ "$(uname)" = "Darwin" ]; then
    START_DATE=$(date -v-400d '+%Y-%m-%d')
  else
    START_DATE=$(date -d '400 days ago' '+%Y-%m-%d')
  fi
  CUSTOM_FLAG=false
fi

export START_DATE END_DATE CUSTOM_FLAG

# 2) Python 계산
python3 << 'PYCODE'
import os, warnings
warnings.filterwarnings("ignore", category=FutureWarning)
import yfinance as yf
from datetime import datetime, timedelta

tickers = ["SOXL","TMF","SCHD","JEPI","JEPQ","QQQ","SPLG","NVDA","TQQQ"]
std_windows = [10,20,60,90,120,252]

start = os.environ["START_DATE"]
end   = os.environ["END_DATE"]
custom = os.environ["CUSTOM_FLAG"].lower() == "true"
fmt = "%Y-%m-%d"
end_adj = (datetime.strptime(end, fmt) + timedelta(days=1)).strftime(fmt)

# 1) 전일 종가 가져오기 (period=1d → 항상 어제 종가)
prev_close = {}
for t in tickers:
    hist = yf.download(t, period="1d", auto_adjust=False, progress=False)["Close"].dropna()
    prev_close[t] = float(hist.iloc[-1]) if not hist.empty else None

# 2) 기준일(Base_date)
base = yf.download(tickers[0], start=start, end=end_adj,
                   auto_adjust=True, progress=False)["Close"].dropna()
print(f"@Base_date: {base.index[-1].strftime(fmt)}\n")

# 3) σ 계산 및 출력
for t in tickers:
    data = yf.download(t, start=start, end=end_adj,
                       auto_adjust=True, progress=False)["Close"].dropna()
    rets = data.pct_change().dropna()
    pc = prev_close.get(t)
    if pc is None:
        print(f"{t}: 종가 조회 실패\n")
        continue

    print(f"{t:>4s} {'종가':>4s} {'1σ':>6s} {'2σ':>6s} {'σ(%)':>7s}")
    for w in std_windows:
        if len(rets) < w: continue
        s = float(rets.tail(w).std()); pct = s * 100
        p1, p2 = pc*(1-s), pc*(1-2*s)
        print(f"{w:4d} {pc:6.2f} {p1:6.2f} {p2:6.2f} {pct:5.2f}%")
        
    if custom:
        s = float(rets.std()); pct = s * 100
        p1, p2 = pc*(1-s), pc*(1-2*s)
        print(f"{'c':>4s} {pc:6.2f} {p1:6.2f} {p2:6.2f} {pct:6.2f}%")

    print()
PYCODE
