import pandas as pd
import numpy as np
from risk_manager import RiskManager
from strategies import orb_signal, vwap_signal
import random

risk = RiskManager()

def generate_fake_data():
    data = pd.DataFrame({
        "close": np.random.normal(100, 1, 20),
        "high": np.random.normal(101, 1, 20),
        "low": np.random.normal(99, 1, 20),
        "volume": np.random.randint(100, 1000, 20)
    })
    return data

def fake_trade():
    return random.choice([50, -50, 75, -75])

def run():
    for i in range(20):
        data = generate_fake_data()

        for name, func in [("ORB", orb_signal), ("VWAP", vwap_signal)]:
            signal = func(data)
            if not signal:
                continue

            order_risk = random.choice([40, 60, 80])
            ok, reason = risk.can_trade(order_risk)

            if not ok:
                print(name, "BLOCKED:", reason)
                continue

            risk.open_positions += 1
            pnl = fake_trade()
            risk.update(pnl)
            risk.open_positions -= 1

            print(name, signal, "PNL:", pnl, "Equity:", risk.current_equity)

run()
