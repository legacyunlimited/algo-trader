import yfinance as yf
import pandas as pd
from datetime import datetime
from strategies import detect_market_regime, mean_reversion_signal, trend_following_signal, calculate_atr, session_vwap

print("="*60)
print("CURRENT MARKET CONDITIONS CHECK")
print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*60)

for symbol in ['SPY', 'QQQ']:
    print(f"\n{symbol}:")
    print("-"*40)
    
    # Get latest data
    df = yf.download(symbol, period='1d', interval='5m', progress=False)
    
    if df.empty:
        print("  No data available")
        continue
    
    df = df.reset_index()
    df.columns = ['datetime', 'open', 'high', 'low', 'close', 'volume']
    df['datetime'] = pd.to_datetime(df['datetime'])
    df['date'] = df['datetime'].dt.date
    df['atr'] = calculate_atr(df)
    
    current_price = df['close'].iloc[-1]
    current_atr = df['atr'].iloc[-1]
    
    print(f"  Current Price: ${current_price:.2f}")
    print(f"  Current ATR: ${current_atr:.2f}")
    print(f"  Volume: {df['volume'].iloc[-1]:,.0f}")
    
    # Calculate VWAP
    try:
        vwap = session_vwap(df)
        current_vwap = vwap.iloc[-1]
        distance = (current_price - current_vwap) / current_atr
        print(f"  VWAP: ${current_vwap:.2f}")
        print(f"  Distance from VWAP: {distance:.2f} ATR")
    except:
        pass
    
    # Check regime
    regime = detect_market_regime(df)
    print(f"  Market Regime: {regime}")
    
    # Check signals
    signal = mean_reversion_signal(df, df)
    if signal:
        print(f"  ⚡ MEAN REVERSION SIGNAL: {signal}")
    else:
        print(f"  No mean reversion signal")
    
    signal2 = trend_following_signal(df, df)
    if signal2:
        print(f"  ⚡ TREND SIGNAL: {signal2}")
    else:
        print(f"  No trend signal")
    
    # Check thresholds
    print(f"\n  Signal Requirements:")
    print(f"    - Need price >0.9 ATR from VWAP (currently: {abs(distance):.2f})" if 'distance' in locals() else "")
    print(f"    - Need volume >1.2x average")
    
    avg_volume = df['volume'].tail(20).mean()
    current_vol = df['volume'].iloc[-1]
    vol_ratio = current_vol / avg_volume if avg_volume > 0 else 0
    print(f"    - Volume ratio: {vol_ratio:.2f}x (need >1.2x)")

print("\n" + "="*60)
print("Note: The market just opened. It may take 30-60 minutes")
print("for price to stretch to extreme levels.")
print("="*60)
