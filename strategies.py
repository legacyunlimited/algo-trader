import numpy as np
import pandas as pd

from config import (
    ATR_PERIOD,
    ADX_TREND_THRESHOLD,
    SLOPE_TREND_THRESHOLD_ATR,
    REVERSION_DISTANCE_ATR,
    TREND_PULLBACK_ATR,
    TREND_MIN_SLOPE_ATR,
    MIN_VOLUME_RATIO,
    SYMBOL_SETTINGS,
)

def calculate_atr(data: pd.DataFrame, period: int = ATR_PERIOD) -> pd.Series:
    high_low = data["high"] - data["low"]
    high_close = (data["high"] - data["close"].shift(1)).abs()
    low_close = (data["low"] - data["close"].shift(1)).abs()
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = true_range.rolling(period).mean()
    return atr

def calculate_adx(data: pd.DataFrame, period: int = 14) -> float:
    if len(data) < period + period:
        return 0.0
    high = data["high"]
    low = data["low"]
    close = data["close"]
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    up_move = high - high.shift(1)
    down_move = low.shift(1) - low
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
    atr_smooth = tr.rolling(period).mean()
    plus_di = 100 * (pd.Series(plus_dm).rolling(period).mean() / atr_smooth)
    minus_di = 100 * (pd.Series(minus_dm).rolling(period).mean() / atr_smooth)
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    adx = dx.rolling(period).mean()
    return float(adx.iloc[-1]) if not pd.isna(adx.iloc[-1]) else 0.0

def calculate_ema(data: pd.DataFrame, period: int) -> pd.Series:
    return data["close"].ewm(span=period, adjust=False).mean()

def calculate_macd(data: pd.DataFrame) -> tuple:
    ema12 = data["close"].ewm(span=12, adjust=False).mean()
    ema26 = data["close"].ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    histogram = macd - signal
    return macd, signal, histogram

def session_vwap(data: pd.DataFrame) -> pd.Series:
    typical_price = (data["high"] + data["low"] + data["close"]) / 3.0
    tpv = typical_price * data["volume"]
    if "date" not in data.columns:
        if "datetime" in data.columns:
            data = data.copy()
            data["date"] = data["datetime"].dt.date
        else:
            data = data.copy()
            data["date"] = data.index.date
    cum_tpv = tpv.groupby(data["date"]).cumsum()
    cum_vol = data["volume"].groupby(data["date"]).cumsum()
    vwap = cum_tpv / cum_vol
    vwap = vwap.replace([np.inf, -np.inf], np.nan)
    return vwap

def detect_market_regime(data: pd.DataFrame, symbol: str = None) -> str:
    if len(data) < 50:
        return "SIDEWAYS"
    ema20 = calculate_ema(data, 20)
    ema50 = calculate_ema(data, 50)
    atr = calculate_atr(data, ATR_PERIOD)
    adx = calculate_adx(data, 14)
    current_atr = atr.iloc[-1]
    if current_atr == 0 or pd.isna(current_atr):
        return "SIDEWAYS"
    if len(ema20) >= 6:
        slope = (ema20.iloc[-1] - ema20.iloc[-6]) / 5
        norm_slope = abs(slope) / current_atr
    else:
        norm_slope = 0
    ema_sep = abs(ema20.iloc[-1] - ema50.iloc[-1]) / current_atr if current_atr > 0 else 0
    if len(data) >= 25:
        recent_volume = data["volume"].tail(5).mean()
        prior_volume = data["volume"].tail(25).head(20).mean()
        volume_expansion = recent_volume / prior_volume if prior_volume > 0 else 1.0
    else:
        volume_expansion = 1.0
    if len(atr) >= 6:
        atr_5_ago = atr.iloc[-6]
        atr_expansion = current_atr / atr_5_ago if atr_5_ago > 0 else 1.0
    else:
        atr_expansion = 1.0
    if atr_expansion > 1.2 and volume_expansion > 1.5:
        return "VOLATILE"
    min_adx = ADX_TREND_THRESHOLD
    if symbol and symbol in SYMBOL_SETTINGS:
        min_adx = SYMBOL_SETTINGS[symbol].get("trend_min_adx", ADX_TREND_THRESHOLD)
    if adx > min_adx and norm_slope > 0.25 and ema_sep > 0.15:
        return "TRENDING"
    return "SIDEWAYS"

def volume_confirmed(data: pd.DataFrame, lookback: int = 20) -> bool:
    if len(data) < lookback + 1:
        return True
    current_volume = data["volume"].iloc[-1]
    avg_volume = data["volume"].tail(lookback).mean()
    return current_volume >= avg_volume * MIN_VOLUME_RATIO

def mean_reversion_signal(intraday_data: pd.DataFrame, daily_data: pd.DataFrame, symbol: str = None) -> str:
    if len(intraday_data) < 20 or len(daily_data) < 20:
        return None
    reversion_distance = REVERSION_DISTANCE_ATR
    if symbol and symbol in SYMBOL_SETTINGS:
        reversion_distance = SYMBOL_SETTINGS[symbol].get("reversion_distance_atr", REVERSION_DISTANCE_ATR)
    vwap = session_vwap(intraday_data)
    current_vwap = vwap.iloc[-1]
    current_close = daily_data["close"].iloc[-1]
    current_atr = daily_data["atr"].iloc[-1] if "atr" in daily_data.columns else calculate_atr(daily_data).iloc[-1]
    if pd.isna(current_vwap) or current_atr <= 0:
        return None
    regime = detect_market_regime(daily_data, symbol)
    if regime != "SIDEWAYS":
        return None
    distance_to_vwap = (current_close - current_vwap) / current_atr
    current_open = daily_data["open"].iloc[-1]
    prev_close = daily_data["close"].iloc[-2]
    if distance_to_vwap <= -reversion_distance:
        bullish_reversal = current_close > current_open and current_close > prev_close
        if bullish_reversal and volume_confirmed(daily_data):
            return "LONG"
    if distance_to_vwap >= reversion_distance:
        bearish_reversal = current_close < current_open and current_close < prev_close
        if bearish_reversal and volume_confirmed(daily_data):
            return "SHORT"
    return None

def trend_following_signal(intraday_data: pd.DataFrame, daily_data: pd.DataFrame, symbol: str = None) -> str:
    if len(intraday_data) < 20 or len(daily_data) < 30:
        return None
    min_adx = TREND_MIN_SLOPE_ATR
    if symbol and symbol in SYMBOL_SETTINGS:
        min_adx = SYMBOL_SETTINGS[symbol].get("trend_min_adx", TREND_MIN_SLOPE_ATR)
    atr = calculate_atr(daily_data)
    ema20 = calculate_ema(daily_data, 20)
    ema50 = calculate_ema(daily_data, 50)
    vwap = session_vwap(intraday_data)
    macd, macd_signal, macd_hist = calculate_macd(daily_data)
    current_close = daily_data["close"].iloc[-1]
    current_atr = atr.iloc[-1]
    current_ema20 = ema20.iloc[-1]
    current_ema50 = ema50.iloc[-1]
    current_vwap = vwap.iloc[-1]
    current_macd_hist = macd_hist.iloc[-1]
    if current_atr <= 0 or pd.isna(current_atr):
        return None
    regime = detect_market_regime(daily_data, symbol)
    if regime != "TRENDING":
        return None
    adx = calculate_adx(daily_data, 14)
    if adx < min_adx:
        return None
    if len(ema20) >= 6:
        ema_slope = (current_ema20 - ema20.iloc[-6]) / 5 / current_atr
    else:
        ema_slope = 0
    is_uptrend = (current_ema20 > current_ema50 and ema_slope > 0.1 and current_close > current_ema20 and current_macd_hist > 0)
    if is_uptrend:
        recent_high = daily_data["high"].tail(5).max()
        breakout = current_close > recent_high * 0.998
        if (breakout or current_close > current_vwap) and volume_confirmed(daily_data):
            return "LONG"
    is_downtrend = (current_ema20 < current_ema50 and ema_slope < -0.1 and current_close < current_ema20 and current_macd_hist < 0)
    if is_downtrend:
        recent_low = daily_data["low"].tail(5).min()
        breakdown = current_close < recent_low * 1.002
        if (breakdown or current_close < current_vwap) and volume_confirmed(daily_data):
            return "SHORT"
    return None

def get_stops_and_targets(entry_price: float, side: str, atr: float, regime: str, symbol: str = None) -> tuple:
    if regime == "TRENDING":
        stop_mult = 1.5
        target_mult = 2.5
    else:
        stop_mult = 0.75
        target_mult = 1.2
    if symbol and symbol in SYMBOL_SETTINGS:
        risk_mult = SYMBOL_SETTINGS[symbol].get("max_risk_mult", 1.0)
        if risk_mult < 1.0:
            stop_mult = stop_mult * risk_mult
            target_mult = target_mult * risk_mult
    if side == "LONG":
        stop = entry_price - (stop_mult * atr)
        target = entry_price + (target_mult * atr)
    else:
        stop = entry_price + (stop_mult * atr)
        target = entry_price - (target_mult * atr)
    return stop, target
