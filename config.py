"""
Trading System Configuration
All settings centralized here
"""

# =========================================================
# ACCOUNT & RISK
# =========================================================
ACCOUNT_SIZE = 10000
INITIAL_CAPITAL = 10000
MAX_RISK_PER_TRADE = 0.008  # 0.8% per trade
MAX_TOTAL_RISK = 0.03  # Max 3% total risk across positions
MAX_CORRELATED_RISK = 0.02  # Max 2% risk in correlated assets

DAILY_LOSS_LIMIT_PCT = 0.005  # 0.5% daily loss limit
MAX_DRAWDOWN_PCT = 0.15  # 15% max drawdown before shutdown
MAX_OPEN_POSITIONS = 2
MAX_TRADES_PER_DAY = 8
MAX_TRADES_PER_STRATEGY_PER_DAY = 4

# =========================================================
# MARKET REGIME DETECTION
# =========================================================
ADX_TREND_THRESHOLD = 25
SLOPE_TREND_THRESHOLD_ATR = 0.5
REGIME_LOOKBACK = 20
ADX_PERIOD = 14

# =========================================================
# STRATEGY PARAMETERS (Base)
# =========================================================
ATR_PERIOD = 14
ATR_MIN = 0.15
ATR_MAX = 4.00

# Mean Reversion (Sideways Markets)
REVERSION_DISTANCE_ATR = 0.9
REVERSION_STOP_ATR = 0.75
REVERSION_TARGET_ATR = 1.2
REVERSION_MAX_TREND_SLOPE = 0.35

# Trend Following (Trending Markets)
TREND_PULLBACK_ATR = 0.8
TREND_STOP_ATR = 1.5
TREND_TARGET_ATR = 2.5
TREND_MIN_SLOPE_ATR = 0.15
TREND_MIN_ADX = 20  # ADDED THIS - was missing

# =========================================================
# SYMBOL-SPECIFIC SETTINGS
# =========================================================
SYMBOL_SETTINGS = {
    "SPY": {
        "enabled": True,
        "max_risk_mult": 1.0,
        "reversion_distance_atr": 0.9,
        "trend_min_adx": 20,
    },
    "QQQ": {
        "enabled": True,
        "max_risk_mult": 1.0,
        "reversion_distance_atr": 0.9,
        "trend_min_adx": 20,
    },
    "NVDA": {
        "enabled": False,
        "max_risk_mult": 0.6,
        "reversion_distance_atr": 1.0,
        "trend_min_adx": 25,
    },
    "MSFT": {
        "enabled": False,
        "max_risk_mult": 0.7,
        "reversion_distance_atr": 0.8,
        "trend_min_adx": 22,
    },
    "AMZN": {
        "enabled": False,
        "max_risk_mult": 0.7,
        "reversion_distance_atr": 0.8,
        "trend_min_adx": 22,
    },
}

# =========================================================
# EXECUTION & TIMING
# =========================================================
SESSION_START = "09:30"
LAST_ENTRY_TIME = "15:30"
MAX_HOLD_BARS = 30
MIN_SHARES = 1

# Volume Confirmation
MIN_VOLUME_RATIO = 1.2

# =========================================================
# DATA
# =========================================================
SYMBOLS = ["SPY", "QQQ"]
DATA_PERIOD = "60d"
DATA_INTERVAL = "5m"

# =========================================================
# FEES
# =========================================================
COMMISSION_PER_SHARE = 0.00