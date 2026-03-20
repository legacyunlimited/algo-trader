import pandas as pd

def orb_signal(data):
    # data = DataFrame with OHLC
    first_15 = data.iloc[:3]  # 3 x 5-min candles

    high = first_15['high'].max()
    low = first_15['low'].min()

    current_price = data.iloc[-1]['close']

    if current_price > high:
        return "LONG"
    elif current_price < low:
        return "SHORT"
    else:
        return None


def vwap_signal(data):
    # basic VWAP approximation
    data['vwap'] = (data['close'] * data['volume']).cumsum() / data['volume'].cumsum()

    current_price = data.iloc[-1]['close']
    vwap = data.iloc[-1]['vwap']

    if current_price < vwap * 0.98:
        return "LONG"
    elif current_price > vwap * 1.02:
        return "SHORT"
    else:
        return None
