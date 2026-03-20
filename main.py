import random
from datetime import datetime

import pandas as pd
import yfinance as yf

from risk_manager import RiskManager
from strategies import orb_signal, vwap_signal
from config import ENABLE_ORB, ENABLE_VWAP


risk = RiskManager()


def get_real_data(symbol: str = "SPY", interval: str = "5m", period: str = "1d") -> pd.DataFrame:
    data = yf.download(symbol, interval=interval, period=period, auto_adjust=False, progress=False)

    if data.empty:
        raise ValueError("No market data returned from Yahoo Finance.")

    data = data.rename(
        columns={
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
        }
    )

    # Keep only the columns we need
    needed_cols = ["open", "high", "low", "close", "volume"]
    data = data[needed_cols].dropna()

    if len(data) < 3:
        raise ValueError("Not enough candle data to evaluate strategies.")

    return data


def fake_order_risk() -> float:
    return random.choice([40, 50, 60, 75, 90])


def fake_trade_result() -> float:
    # Still simulated execution/PnL for safety
    return random.choice([75, 50, -50, -75, 30, -30])


def execute_trade(strategy_name: str, signal: str) -> None:
    order_risk = fake_order_risk()
    ok, reason = risk.can_trade(order_risk)
    timestamp = datetime.now().isoformat(timespec="seconds")

    if not ok:
        print(f"[{timestamp}] {strategy_name}: BLOCKED | {reason}")
        return

    risk.open_positions += 1
    pnl = fake_trade_result()
    risk.update(pnl)
    risk.open_positions -= 1

    print(
        f"[{timestamp}] {strategy_name}: {signal} | "
        f"risk={order_risk} | pnl={pnl} | "
        f"equity={risk.current_equity:.2f} | daily_pnl={risk.daily_pnl:.2f}"
    )


def main():
    print("Starting paper-mode prototype with real Yahoo Finance data...\n")

    try:
        data = get_real_data("SPY", "5m", "1d")
        print(f"Loaded {len(data)} candles.\n")
    except Exception as e:
        print(f"DATA ERROR: {e}")
        return

    if ENABLE_ORB:
        try:
            sig = orb_signal(data.copy())
            if sig:
                execute_trade("ORB", sig)
            else:
                print("ORB: No signal")
        except Exception as e:
            print(f"ORB ERROR: {e}")

    if ENABLE_VWAP:
        try:
            sig = vwap_signal(data.copy())
            if sig:
                execute_trade("VWAP", sig)
            else:
                print("VWAP: No signal")
        except Exception as e:
            print(f"VWAP ERROR: {e}")

    print("\nDone.")


if __name__ == "__main__":
    main()
