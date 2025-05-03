#!/usr/bin/env python3
import yfinance as yf
import pandas as pd

def check_std_buy_signal_auto(tickers, period=20, k1=1, k2=2):
    results = []
    for ticker in tickers:
        # 티커별로 Close만 다운로드
        df = yf.download(ticker, period=f"{period*3}d", progress=False)[['Close']].copy()
        df['MA']  = df['Close'].rolling(window=period).mean()
        df['STD'] = df['Close'].rolling(window=period).std()
        df = df.dropna()
        last = df.iloc[-1]
        price = float(last['Close'])
        ma    = float(last['MA'])
        std   = float(last['STD'])
        l1    = ma - k1 * std
        l2    = ma - k2 * std

        if price < l2:
            sig = "매수(2σ 이하)"
        elif price < l1:
            sig = "매수(1σ 이하)"
        else:
            sig = "대기"

        results.append({
            "Ticker": ticker,
            "현재가": round(price, 2),
            f"{period}일 MA": round(ma, 2),
            f"{period}일 1σ": round(l1, 2),
            f"{period}일 2σ": round(l2, 2),
            "신호": sig
        })
    return pd.DataFrame(results)

if __name__ == "__main__":
    tickers = ["SOXL","SCHD","JEPI","JEPQ","QQQ","SPLG","TMF","NVDA"]

    # 20일 기준
    df20 = check_std_buy_signal_auto(tickers, period=20)
    print("\n===== 20일(1개월) 기준 매수 신호 =====")
    print(df20.to_string(index=False))

    # 252일(1년) 기준
    df252 = check_std_buy_signal_auto(tickers, period=252)
    print("\n===== 252일(1년) 기준 매수 신호 =====")
    print(df252.to_string(index=False))
