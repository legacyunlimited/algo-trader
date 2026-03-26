import pandas as pd
import time
import os
from datetime import datetime

def clear_screen():
    os.system('clear' if os.name == 'posix' else 'cls')

def show_dashboard():
    while True:
        clear_screen()
        print("="*60)
        print(f"TRADING DASHBOARD - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
        try:
            df = pd.read_csv('trade_log.csv')
            if not df.empty:
                total_trades = len(df)
                winning_trades = len(df[df['pnl'] > 0])
                win_rate = winning_trades / total_trades * 100 if total_trades > 0 else 0
                total_pnl = df['pnl'].sum()
                
                print(f"\n📊 TRADE STATISTICS")
                print(f"   Total Trades: {total_trades}")
                print(f"   Win Rate: {win_rate:.1f}%")
                print(f"   Total P&L: ${total_pnl:.2f}")
                
                print(f"\n📝 LAST 5 TRADES")
                last_trades = df.tail(5)[['timestamp', 'strategy', 'signal', 'pnl']]
                print(last_trades.to_string(index=False))
            else:
                print("\n   No trades yet...")
        except FileNotFoundError:
            print("\n   No trade log found. Bot may not have started yet.")
        except Exception as e:
            print(f"\n   Error: {e}")
        
        print("\n" + "="*60)
        print("Dashboard updates every 10 seconds | Ctrl+C to exit")
        time.sleep(10)

if __name__ == "__main__":
    try:
        show_dashboard()
    except KeyboardInterrupt:
        print("\nDashboard stopped")
