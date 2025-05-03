#!/usr/bin/env python3
import yfinance as yf
import pandas as pd

def check_std_buy_signal_auto(tickers, period=20, k1=1, k2=2):
    results = []
    # 과거 데이터를 충분히 받기 위해 period*3일치 다운로드
    df = yf.download(tickers, period=f"{period*3}d", group_by='ticker', progress=False)
    for ticker in tickers:
        data = df[ticker] if isinstance(df, dict) else df
        close = data['Close']
        ma = close.rolling(window=period).mean()
        std = close.rolling(window=period).std()
        latest = data.iloc[-1]['Close']
        latest_ma = ma.iloc[-1]
        latest_std = std.iloc[-1]
        l1 = latest_ma - k1 * latest_std
        l2 = latest_ma - k2 * latest_std
        if latest < l2:
            sig = "매수(2σ 이하)"
        elif latest < l1:
            sig = "매수(1σ 이하)"
        else:
            sig = "대기"
        results.append({
            "Ticker": ticker,
            "현재가": round(latest, 2),
            f"{period}일 MA": round(latest_ma, 2),
            f"{period}일 1σ": round(l1, 2),
            f"{period}일 2σ": round(l2, 2),
            "신호": sig
        })
    return pd.DataFrame(results)

if __name__ == "__main__":
    tickers = ["SOXL","SCHD","JEPI","JEPQ","QQQ","SPLG","TMF","NVDA"]

    # ① 20일 기준
    df20 = check_std_buy_signal_auto(tickers, period=20)
    print("\n===== 20일(1개월) 기준 매수 신호 =====")
    print(df20.to_string(index=False))

    # ② 252일(1년) 기준
    df252 = check_std_buy_signal_auto(tickers, period=252)
    print("\n===== 252일(1년) 기준 매수 신호 =====")
    print(df252.to_string(index=False))
