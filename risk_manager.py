import pandas as pd
from collections import defaultdict
from typing import Tuple, Optional
from dataclasses import dataclass, field

from config import (
    ACCOUNT_SIZE,
    MAX_RISK_PER_TRADE,
    MAX_TOTAL_RISK,
    MAX_CORRELATED_RISK,
    DAILY_LOSS_LIMIT_PCT,
    MAX_DRAWDOWN_PCT,
    MAX_OPEN_POSITIONS,
    MAX_TRADES_PER_DAY,
    MAX_TRADES_PER_STRATEGY_PER_DAY,
)


@dataclass
class Position:
    symbol: str
    strategy: str
    entry_price: float
    shares: int
    risk_amount: float
    entry_time: pd.Timestamp


class RiskManager:
    def __init__(self, initial_equity: float = ACCOUNT_SIZE):
        self.initial_equity = initial_equity
        self.peak_equity = initial_equity
        self.current_equity = initial_equity
        self.daily_start_equity = initial_equity
        self.daily_pnl = 0.0
        self.day_halted = False
        self.trading_enabled = True
        self.current_day = None
        
        self.open_positions: dict[str, Position] = {}
        self.total_risk = 0.0
        self.daily_trade_count = 0
        self.daily_strategy_count = defaultdict(int)
        
        # Correlation groups (simplified)
        self.correlation_groups = {
            "tech": ["QQQ", "NVDA", "MSFT", "AMZN"],
            "broad": ["SPY"],
        }
    
    def _get_correlation_group(self, symbol: str) -> Optional[str]:
        for group, symbols in self.correlation_groups.items():
            if symbol in symbols:
                return group
        return None
    
    def _correlated_risk(self, symbol: str, new_risk: float) -> float:
        """Calculate total risk in same correlation group"""
        group = self._get_correlation_group(symbol)
        if not group:
            return new_risk
        
        total = new_risk
        for pos in self.open_positions.values():
            if self._get_correlation_group(pos.symbol) == group:
                total += pos.risk_amount
        return total
    
    def update_day(self, timestamp: pd.Timestamp):
        day = timestamp.date()
        
        if self.current_day is None:
            self.current_day = day
            self.daily_start_equity = self.current_equity
            return
        
        if day != self.current_day:
            # New day: reset daily limits
            self.current_day = day
            self.daily_start_equity = self.current_equity
            self.daily_pnl = 0.0
            self.day_halted = False
            self.daily_trade_count = 0
            self.daily_strategy_count = defaultdict(int)
    
    def update_equity(self, pnl: float):
        """Update equity after trade close"""
        self.current_equity += pnl
        self.daily_pnl += pnl
        
        # Update peak equity for drawdown
        if self.current_equity > self.peak_equity:
            self.peak_equity = self.current_equity
        
        # Check daily loss limit
        daily_loss_limit = self.daily_start_equity * DAILY_LOSS_LIMIT_PCT
        if self.daily_pnl <= -daily_loss_limit:
            self.day_halted = True
        
        # Check max drawdown
        if self.drawdown() >= MAX_DRAWDOWN_PCT:
            self.trading_enabled = False
    
    def register_entry(self, symbol: str, strategy: str, entry_price: float, 
                       shares: int, risk_amount: float, timestamp: pd.Timestamp):
        """Register a new position"""
        self.open_positions[symbol] = Position(
            symbol=symbol,
            strategy=strategy,
            entry_price=entry_price,
            shares=shares,
            risk_amount=risk_amount,
            entry_time=timestamp,
        )
        self.total_risk += risk_amount
        self.daily_trade_count += 1
        self.daily_strategy_count[strategy] += 1
    
    def register_exit(self, symbol: str):
        """Remove a position"""
        if symbol in self.open_positions:
            self.total_risk -= self.open_positions[symbol].risk_amount
            del self.open_positions[symbol]
    
    def drawdown(self) -> float:
        """Current drawdown from peak"""
        if self.peak_equity == 0:
            return 0.0
        return (self.peak_equity - self.current_equity) / self.peak_equity
    
    def can_trade(self, symbol: str, risk_amount: float, strategy: str, 
                  timestamp: pd.Timestamp) -> Tuple[bool, str]:
        """Check if a new trade is allowed"""
        
        # Update day first
        self.update_day(timestamp)
        
        # Global checks
        if not self.trading_enabled:
            return False, "Trading disabled: max drawdown hit"
        
        if self.day_halted:
            return False, "Daily loss limit hit"
        
        # Position limits
        if len(self.open_positions) >= MAX_OPEN_POSITIONS:
            return False, f"Max open positions ({MAX_OPEN_POSITIONS}) reached"
        
        # Total risk check
        if self.total_risk + risk_amount > self.current_equity * MAX_TOTAL_RISK:
            return False, "Total risk limit would be exceeded"
        
        # Correlated risk check
        correlated_risk = self._correlated_risk(symbol, risk_amount)
        if correlated_risk > self.current_equity * MAX_CORRELATED_RISK:
            return False, "Correlated risk limit would be exceeded"
        
        # Per-trade risk
        max_risk_per_trade = self.current_equity * MAX_RISK_PER_TRADE
        if risk_amount > max_risk_per_trade:
            return False, f"Risk per trade (${risk_amount:.2f}) exceeds limit (${max_risk_per_trade:.2f})"
        
        # Daily trade limits
        if self.daily_trade_count >= MAX_TRADES_PER_DAY:
            return False, f"Max daily trades ({MAX_TRADES_PER_DAY}) reached"
        
        if self.daily_strategy_count[strategy] >= MAX_TRADES_PER_STRATEGY_PER_DAY:
            return False, f"Max {strategy} trades per day ({MAX_TRADES_PER_STRATEGY_PER_DAY}) reached"
        
        return True, "Approved"
    
    def get_position_size(self, entry_price: float, stop_price: float) -> int:
        """Calculate position size based on risk"""
        risk_per_share = abs(entry_price - stop_price)
        if risk_per_share <= 0:
            return 0
        
        max_risk_dollars = self.current_equity * MAX_RISK_PER_TRADE
        shares = int(max_risk_dollars / risk_per_share)
        return max(shares, 0)
    
    def get_equity(self) -> float:
        return self.current_equity
    
    def get_open_positions(self) -> list:
        return list(self.open_positions.values())