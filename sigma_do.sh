#!/usr/bin/env bash
set -euo pipefail

# 1) 기간 파싱
if [ "$#" -eq 2 ]; then
  SD="20${1:0:2}-${1:2:2}-${1:4:2}"
  ED="20${2:0:2}-${2:2:2}-${2:4:2}"
else
  ED="$(date '+%Y-%m-%d')"
  if [ "$(uname)" = "Darwin" ]; then
    SD="$(date -v-400d '+%Y-%m-%d')"
  else
    SD="$(date -d '400 days ago' '+%Y-%m-%d')"
  fi
fi

# 2) Python 으로 KRX 데이터 불러와 σ 계산
python3 << 'PYCODE'
import os
from datetime import datetime, timedelta
from pykrx import stock

sd      = os.getenv("SD")
ed      = os.getenv("ED")
ed_next = (datetime.strptime(ed, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")

categories = {
    "ISA": [
        ("KODEX 미국나스닥100", "379810"),
        ("ACE 미국배당다우존스", "402970"),
        ("KODEX 미국배당커버드콜액티브", "441640"),
    ],
    "세공(연저)": [
        ("ACE 미국S&P500", "360200"),
        ("ACE 미국배당다우존스", "402970"),
        ("TIGER 미국나스닥100타겟데일리커버드콜", "486290"),
        ("KODEX 200타겟위클리커버드콜", "498400"),
    ],
    "안세공(연저)": [
        ("TIGER 은행고배당플러스TOP10", "466940"),
        ("KODEX 미국배당다우존스", "489250"),
        ("KODEX 미국배당커버드콜액티브", "441640"),
        ("KODEX 미국S&P500", "379800"),
    ],
}

windows = [10,20,60,90,120,252]

print(f"📅 Base_date : {ed}\\n")
for cat, etfs in categories.items():
    print(f"📍 {cat}\\n")
    for name, code in etfs:
        df = stock.get_market_ohlcv_by_date(sd, ed_next, code)
        if "종가" not in df or df["종가"].empty:
            print(f"✓ {name} ({code}): 종가 조회 실패\\n")
            continue

        pc   = float(df["종가"].iloc[-1])
        rets = df["종가"].pct_change().dropna()

        print(f"✓ {name} ({code})")
        # 헤더: 간격 최소화
        print(f"{'기간':>3s} {'종가':>3s} {'1σ':>5s} {'2σ':>5s} {'σ(%)':>5s}")
        for w in windows:
            if len(rets) < w: continue
            s   = rets.tail(w).std()
            pct = s * 100
            p1  = pc * (1 - s)
            p2  = pc * (1 - 2*s)
            # 데이터 행: 천단위 콤마, 소수점 없음
            print(f"{w:>3d} {pc:>7,.0f} {p1:>7,.0f} {p2:>7,.0f} {pct:>5.2f}%")
        print()
PYCODE
