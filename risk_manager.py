from config import *

class RiskManager:
    def __init__(self):
        self.start_equity = ACCOUNT_SIZE
        self.current_equity = ACCOUNT_SIZE
        self.daily_pnl = 0
        self.open_positions = 0

    def can_trade(self, order_risk):
        if self.daily_pnl <= -DAILY_LOSS_LIMIT:
            return False, "Daily loss hit"

        if self.open_positions >= MAX_OPEN_POSITIONS:
            return False, "Too many positions"

        if order_risk > self.current_equity * MAX_RISK_PER_TRADE:
            return False, "Risk too high"

        return True, "Approved"

    def update(self, pnl):
        self.current_equity += pnl
        self.daily_pnl += pnl
