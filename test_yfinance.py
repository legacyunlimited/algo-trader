import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

print("Testing yfinance data access...")

end = datetime.now()
start = end - timedelta(days=2)

print(f"Downloading SPY data from {start} to {end}")

df = yf.download(
    'SPY',
    start=start,
    end=end,
    interval='5m',
    progress=False,
    prepost=False,
    auto_adjust=False
)

print(f"\nDataFrame shape: {df.shape}")
print(f"Columns: {list(df.columns)}")
print(f"\nFirst few rows:")
print(df.head())
print(f"\nLast few rows:")
print(df.tail())
