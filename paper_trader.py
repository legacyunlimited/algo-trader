import pandas as pd
import yfinance as yf
import time
from datetime import datetime, timedelta
import signal
import sys

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

from config import SYMBOLS, MAX_RISK_PER_TRADE, MAX_OPEN_POSITIONS, INITIAL_CAPITAL, MAX_DRAWDOWN_PCT
from risk_manager import RiskManager
from strategies import detect_market_regime, mean_reversion_signal, trend_following_signal, get_stops_and_targets, volume_confirmed, calculate_atr
from logger import init_log, log_trade
from alpaca_config import ALPACA_API_KEY, ALPACA_SECRET_KEY, ALPACA_BASE_URL

class AlpacaPaperTrader:
    def __init__(self):
        if ALPACA_API_KEY == "PKXXXXXXXXXXXXXXXXXX":
            print("\n❌ ERROR: Update alpaca_config.py with your API keys")
            sys.exit(1)
        
        self.trading_client = TradingClient(ALPACA_API_KEY, ALPACA_SECRET_KEY, paper=True)
        self.risk_manager = RiskManager(INITIAL_CAPITAL)
        self.positions = {}
        self.running = True
        
        try:
            account = self.trading_client.get_account()
            print(f"\n✓ Connected to Alpaca Paper Trading")
            print(f"  Portfolio Value: ${float(account.portfolio_value):,.2f}")
        except Exception as e:
            print(f"\n❌ Failed to connect: {e}")
            sys.exit(1)
        
        print(f"\n🤖 Bot starting. Monitoring: {SYMBOLS}")
        init_log()
    
    def shutdown(self, signum, frame):
        print("\n🛑 Shutting down...")
        self.running = False
        sys.exit(0)
    
    def get_live_data(self, symbol):
        try:
            df = yf.download(symbol, period='1d', interval='5m', progress=False)
            if df.empty:
                return df
            df = df.reset_index()
            df.columns = ['datetime', 'open', 'high', 'low', 'close', 'volume']
            df['datetime'] = pd.to_datetime(df['datetime'])
            df['date'] = df['datetime'].dt.date
            df['atr'] = calculate_atr(df)
            return df
        except Exception as e:
            print(f"  Error getting data: {e}")
            return pd.DataFrame()
    
    def check_market_hours(self):
        now = datetime.now()
        if now.weekday() >= 5:
            return False
        market_open = now.replace(hour=9, minute=30, second=0)
        market_close = now.replace(hour=16, minute=0, second=0)
        return market_open <= now <= market_close
    
    def run(self):
        signal.signal(signal.SIGINT, self.shutdown)
        print("\n🤖 Bot running. Press Ctrl+C to stop\n")
        
        last_minute = -1
        
        while self.running:
            try:
                current_time = datetime.now()
                current_minute = current_time.minute
                market_open = self.check_market_hours()
                
                if market_open and current_minute % 5 == 0 and current_minute != last_minute:
                    last_minute = current_minute
                    print(f"\n📊 STATUS @ {current_time.strftime('%H:%M')}")
                    print(f"   Equity: ${self.risk_manager.get_equity():,.2f}")
                    print(f"   Open Positions: {len(self.positions)}")
                    
                    if len(self.positions) < MAX_OPEN_POSITIONS:
                        for symbol in SYMBOLS:
                            if symbol in self.positions:
                                continue
                            data = self.get_live_data(symbol)
                            if data.empty or len(data) < 20:
                                continue
                            
                            regime = detect_market_regime(data, symbol)
                            signal = None
                            
                            if regime == "TRENDING":
                                signal = trend_following_signal(data, data, symbol)
                            elif regime == "SIDEWAYS":
                                signal = mean_reversion_signal(data, data, symbol)
                            
                            if signal:
                                print(f"  📈 Signal: {symbol} {signal}")
                
                time.sleep(10)
                
            except KeyboardInterrupt:
                self.shutdown(None, None)
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                time.sleep(60)

if __name__ == "__main__":
    trader = AlpacaPaperTrader()
    trader.run()
