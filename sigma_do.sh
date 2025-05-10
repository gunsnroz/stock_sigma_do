#!/usr/bin/env bash
#
# Usage: ./sigma_do.sh [YYMMDD YYMMDD]
#  (예) ./sigma_do.sh
#       ./sigma_do.sh 240101 240531
set -euo pipefail

#
# ── 1) 날짜 파싱 ───────────────────────────────────────────────────
#
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

#
# ── 2) Python 로직 ───────────────────────────────────────────────
#
python3 <<'PYCODE'
import os
from datetime import datetime, timedelta
from pykrx import stock

sd = os.getenv("SD")
ed = os.getenv("ED")
# API 는 end_date exclusive
ed_next = (datetime.strptime(ed, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")

# 포트폴리오 설정
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
        ("KODEX 미국배당다우존스",   "489250"),
        ("KODEX 미국배당커버드콜액티브", "441640"),
        ("KODEX 미국S&P500",        "379800"),
    ],
}

windows = [10,20,60,90,120,252]

print(f"📅 Base_date : {ed}\n")
for cat, etfs in categories.items():
    print(f"📍 {cat}\n")
    for name, code in etfs:
        df = stock.get_market_ohlcv_by_date(sd, ed_next, code)
        if "종가" not in df or df["종가"].empty:
            print(f"✓ {name} ({code}): 종가 조회 실패\n")
            continue
        pc = float(df["종가"].iloc[-1])
        rets = df["종가"].pct_change().dropna()

        print(f"✓ {name} ({code})")
        # 좁은 헤더
        print(f"{'기간':>3s} {'종가':>7s} {'1σ':>7s} {'2σ':>7s} {'σ(%)':>6s}")
        for w in windows:
            if len(rets) < w: continue
            s   = rets.tail(w).std()
            pct = s * 100
            p1  = pc * (1 - s)
            p2  = pc * (1 - 2*s)
            print(f"{w:>3d} {pc:>7,.0f} {p1:>7,.0f} {p2:>7,.0f} {pct:>6.2f}%")
        print()
PYCODE
