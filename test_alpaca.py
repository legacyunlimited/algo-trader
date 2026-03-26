from alpaca.trading.client import TradingClient
from alpaca_config import ALPACA_API_KEY, ALPACA_SECRET_KEY

print("Testing Alpaca connection...")
print(f"API Key: {ALPACA_API_KEY[:10]}...")

try:
    trading_client = TradingClient(ALPACA_API_KEY, ALPACA_SECRET_KEY, paper=True)
    account = trading_client.get_account()
    print(f"\n✅ Connected successfully!")
    print(f"Account ID: {account.id}")
    print(f"Equity: ${float(account.equity):,.2f}")
    print(f"Cash: ${float(account.cash):,.2f}")
    print(f"Buying Power: ${float(account.buying_power):,.2f}")
except Exception as e:
    print(f"\n❌ Connection failed: {e}")
