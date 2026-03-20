from risk_manager import RiskManager
from strategies import orb_signal, vwap_signal
import random

risk = RiskManager()

def fake_trade():
    return random.choice([50, -50, 75, -75])

def run():
    for i in range(20):
        for strategy, func in [("ORB", orb_signal), ("VWAP", vwap_signal)]:
            signal = func()
            if not signal:
                continue

            order_risk = random.choice([40, 60, 80])
            ok, reason = risk.can_trade(order_risk)

            if not ok:
                print(strategy, "BLOCKED:", reason)
                continue

            risk.open_positions += 1
            pnl = fake_trade()
            risk.update(pnl)
            risk.open_positions -= 1

            print(strategy, signal, "PNL:", pnl, "Equity:", risk.current_equity)

run()
