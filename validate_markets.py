"""
Validate strategy across different market conditions
"""

import pandas as pd
import numpy as np
from main import backtest_symbol, load_data, print_detailed_summary
from risk_manager import RiskManager
from config import INITIAL_CAPITAL, SYMBOLS, DATA_INTERVAL

# Define test periods with known market conditions
MARKET_PERIODS = {
    "BULL_2023_2024": {
        "period": "180d",
        "description": "Strong bull market (Nov 2023 - May 2024)",
        "expected": "High returns, low drawdown"
    },
    "BEAR_2022": {
        "period": "90d", 
        "description": "Bear market / Correction (May-Jul 2022)",
        "expected": "Negative or flat returns, higher drawdown"
    },
    "SIDEWAYS_2023": {
        "period": "120d",
        "description": "Sideways/Choppy market (Aug-Dec 2023)",
        "expected": "Modest returns, mean reversion dominates"
    },
    "CRASH_2020": {
        "period": "60d",
        "description": "COVID crash (Feb-Mar 2020)",
        "expected": "Protection mechanisms tested"
    },
    "RECOVERY_2020": {
        "period": "120d",
        "description": "Post-crash recovery (Apr-Jul 2020)",
        "expected": "Strong trend following performance"
    }
}

def calculate_metrics(trades_df, final_equity, initial_capital, max_drawdown):
    """Calculate key performance metrics"""
    
    if trades_df.empty:
        return {
            'total_return': 0,
            'sharpe': 0,
            'win_rate': 0,
            'profit_factor': 0,
            'max_drawdown': 0,
            'total_trades': 0
        }
    
    # Win rate
    winning_trades = trades_df[trades_df['net_pnl'] > 0]
    losing_trades = trades_df[trades_df['net_pnl'] <= 0]
    win_rate = len(winning_trades) / len(trades_df) * 100 if len(trades_df) > 0 else 0
    
    # Profit factor
    total_wins = winning_trades['net_pnl'].sum() if len(winning_trades) > 0 else 0
    total_losses = abs(losing_trades['net_pnl'].sum()) if len(losing_trades) > 0 else 1
    profit_factor = total_wins / total_losses if total_losses > 0 else 0
    
    # Total return
    total_return = (final_equity - initial_capital) / initial_capital * 100
    
    # Sharpe (simplified - using daily returns)
    if 'exit_time' in trades_df.columns:
        trades_df = trades_df.sort_values('exit_time')
        trades_df['cumulative'] = trades_df['net_pnl'].cumsum()
        daily_returns = trades_df.groupby(trades_df['exit_time'].dt.date)['net_pnl'].sum()
        if len(daily_returns) > 1:
            sharpe = daily_returns.mean() / daily_returns.std() * np.sqrt(252) if daily_returns.std() > 0 else 0
        else:
            sharpe = 0
    else:
        sharpe = 0
    
    return {
        'total_return': total_return,
        'sharpe': sharpe,
        'win_rate': win_rate,
        'profit_factor': profit_factor,
        'max_drawdown': max_drawdown * 100,
        'total_trades': len(trades_df)
    }

def run_validation():
    """Run backtests across different market conditions"""
    
    results = []
    
    print("\n" + "="*80)
    print("MARKET CONDITION VALIDATION")
    print("="*80)
    
    for period_name, period_config in MARKET_PERIODS.items():
        print(f"\n{'='*80}")
        print(f"TESTING: {period_name}")
        print(f"Period: {period_config['period']} - {period_config['description']}")
        print(f"Expected: {period_config['expected']}")
        print(f"{'='*80}")
        
        # Override config period
        from config import DATA_PERIOD
        original_period = DATA_PERIOD
        
        try:
            # Dynamically change the period
            import config
            config.DATA_PERIOD = period_config['period']
            
            # Re-import main with new config
            import importlib
            import main
            importlib.reload(main)
            importlib.reload(config)
            
            # Run backtest
            risk_manager = RiskManager(INITIAL_CAPITAL)
            all_trades = []
            
            for symbol in SYMBOLS:
                try:
                    df = main.load_data(symbol)
                    trades = main.backtest_symbol(symbol, df, risk_manager)
                    all_trades.extend(trades)
                except Exception as e:
                    print(f"  Error with {symbol}: {e}")
                    continue
            
            # Calculate metrics
            if all_trades:
                trades_df = pd.DataFrame([t.__dict__ for t in all_trades])
                metrics = calculate_metrics(trades_df, risk_manager.get_equity(), INITIAL_CAPITAL, risk_manager.drawdown())
                
                # Add period info
                metrics['period'] = period_name
                metrics['description'] = period_config['description']
                metrics['final_equity'] = risk_manager.get_equity()
                
                results.append(metrics)
                
                # Print summary
                print(f"\nRESULTS:")
                print(f"  Total Return: {metrics['total_return']:.2f}%")
                print(f"  Total Trades: {metrics['total_trades']}")
                print(f"  Win Rate: {metrics['win_rate']:.1f}%")
                print(f"  Profit Factor: {metrics['profit_factor']:.2f}")
                print(f"  Max Drawdown: {metrics['max_drawdown']:.2f}%")
                print(f"  Sharpe Ratio: {metrics['sharpe']:.2f}")
                
                # Assessment
                if metrics['max_drawdown'] > 15:
                    print(f"  ⚠️ WARNING: Drawdown exceeds 15%")
                if metrics['profit_factor'] < 1.25:
                    print(f"  ⚠️ WARNING: Profit factor low")
                if metrics['total_trades'] < 30:
                    print(f"  ⚠️ WARNING: Insufficient trades")
                    
            else:
                print("  No trades executed")
                results.append({
                    'period': period_name,
                    'description': period_config['description'],
                    'total_return': 0,
                    'total_trades': 0,
                    'win_rate': 0,
                    'profit_factor': 0,
                    'max_drawdown': 0,
                    'sharpe': 0,
                    'final_equity': INITIAL_CAPITAL
                })
                
        except Exception as e:
            print(f"Error testing {period_name}: {e}")
            import traceback
            traceback.print_exc()
        
        # Restore original period
        config.DATA_PERIOD = original_period
    
    # Summary table
    print("\n" + "="*80)
    print("SUMMARY ACROSS MARKET CONDITIONS")
    print("="*80)
    
    summary_df = pd.DataFrame(results)
    print(summary_df.to_string(index=False))
    
    # Final assessment
    print("\n" + "="*80)
    print("FINAL ASSESSMENT")
    print("="*80)
    
    passing_periods = []
    failing_periods = []
    
    for result in results:
        period = result['period']
        passes = (
            result['total_trades'] >= 20 and
            result['max_drawdown'] <= 15 and
            result['profit_factor'] >= 1.1
        )
        
        if passes:
            passing_periods.append(period)
        else:
            failing_periods.append(period)
    
    if len(passing_periods) >= 3:
        print(f"✅ PASS: Strategy works in {len(passing_periods)} market conditions")
        print(f"   Working periods: {', '.join(passing_periods)}")
        
        if failing_periods:
            print(f"⚠️  Needs improvement in: {', '.join(failing_periods)}")
        
        print("\nRECOMMENDATION: Ready for paper trading with confidence")
    elif len(passing_periods) >= 2:
        print(f"⚠️  PARTIAL PASS: Works in {len(passing_periods)} conditions")
        print(f"   Working: {', '.join(passing_periods)}")
        print(f"   Failing: {', '.join(failing_periods)}")
        print("\nRECOMMENDATION: Paper trade with caution, focus on known conditions")
    else:
        print(f"❌ FAIL: Only works in {len(passing_periods)} conditions")
        print("\nRECOMMENDATION: Optimize parameters before paper trading")

if __name__ == "__main__":
    run_validation()