"""
COMPLETELY FIXED Monte Carlo Simulation
"""

import pandas as pd
import numpy as np
from main import backtest_symbol, load_data
from risk_manager import RiskManager
from config import INITIAL_CAPITAL, SYMBOLS, DATA_PERIOD
import time
import random

def run_monte_carlo_fixed(iterations=100):
    """Completely fixed Monte Carlo with proper randomization"""
    
    start_time = time.time()
    
    print("\n" + "="*80)
    print("MONTE CARLO SIMULATION - COMPLETELY FIXED")
    print("="*80)
    print(f"Iterations: {iterations}")
    print(f"Symbols: {SYMBOLS}")
    print(f"Period: {DATA_PERIOD}")
    
    # STEP 1: Run ONE backtest to collect all trades
    print("\n[1/2] Running single backtest to collect trades...")
    
    risk_manager = RiskManager(INITIAL_CAPITAL)
    all_trades = []
    
    for symbol in SYMBOLS:
        try:
            df = load_data(symbol)
            trades = backtest_symbol(symbol, df, risk_manager)
            all_trades.extend(trades)
        except Exception as e:
            print(f"  Error with {symbol}: {e}")
            continue
    
    if not all_trades:
        print("No trades found!")
        return None
    
    # Convert to DataFrame
    trades_df = pd.DataFrame([t.__dict__ for t in all_trades])
    original_pnl = trades_df['net_pnl'].values
    original_total = original_pnl.sum()
    original_win_rate = (original_pnl > 0).mean() * 100
    
    print(f"\n     ✓ Collected {len(original_pnl)} trades")
    print(f"     ✓ Original Total PnL: ${original_total:,.2f}")
    print(f"     ✓ Original Win Rate: {original_win_rate:.1f}%")
    
    # STEP 2: Run Monte Carlo by resampling trades WITH REPLACEMENT
    print(f"\n[2/2] Running {iterations} Monte Carlo iterations...")
    print("     (Resampling trades with replacement - true Monte Carlo)")
    
    results = []
    
    for iteration in range(iterations):
        # RESAMPLE with replacement - this creates different total returns
        # Using bootstrap sampling: randomly select trades with replacement
        sample_indices = np.random.choice(len(original_pnl), size=len(original_pnl), replace=True)
        sampled_pnl = original_pnl[sample_indices]
        
        # Calculate cumulative returns
        cumulative = np.cumsum(sampled_pnl)
        
        # Calculate metrics
        final_return = cumulative[-1]
        
        # Calculate max drawdown correctly
        running_peak = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_peak) / INITIAL_CAPITAL * 100
        max_drawdown = drawdown.min()
        
        # Calculate win rate
        win_rate = (sampled_pnl > 0).mean() * 100
        
        # Calculate max consecutive losses
        losses = (sampled_pnl < 0).astype(int)
        consecutive_losses = 0
        max_consecutive_losses = 0
        for loss in losses:
            if loss:
                consecutive_losses += 1
                max_consecutive_losses = max(max_consecutive_losses, consecutive_losses)
            else:
                consecutive_losses = 0
        
        results.append({
            'iteration': iteration,
            'final_return': final_return,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'max_consecutive_losses': max_consecutive_losses,
            'total_trades': len(sampled_pnl)
        })
        
        # Progress indicator
        if (iteration + 1) % 20 == 0:
            print(f"     Progress: {iteration + 1}/{iterations}")
    
    results_df = pd.DataFrame(results)
    
    elapsed = time.time() - start_time
    print(f"\n✓ Monte Carlo complete in {elapsed/60:.1f} minutes")
    
    # Print results
    print("\n" + "="*80)
    print("MONTE CARLO RESULTS")
    print("="*80)
    
    # Final Return Statistics
    print(f"\nFINAL RETURN (Total PnL):")
    print(f"  Original: ${original_total:,.2f}")
    print(f"  Mean:     ${results_df['final_return'].mean():,.2f}")
    print(f"  Median:   ${results_df['final_return'].median():,.2f}")
    print(f"  Std Dev:  ${results_df['final_return'].std():,.2f}")
    print(f"  Min:      ${results_df['final_return'].min():,.2f}")
    print(f"  Max:      ${results_df['final_return'].max():,.2f}")
    
    # Confidence intervals
    percentile_10 = np.percentile(results_df['final_return'], 10)
    percentile_25 = np.percentile(results_df['final_return'], 25)
    percentile_75 = np.percentile(results_df['final_return'], 75)
    percentile_90 = np.percentile(results_df['final_return'], 90)
    
    print(f"\nCONFIDENCE INTERVALS:")
    print(f"  50% CI: ${percentile_25:,.2f} to ${percentile_75:,.2f}")
    print(f"  80% CI: ${percentile_10:,.2f} to ${percentile_90:,.2f}")
    
    # Drawdown statistics
    print(f"\nMAX DRAWDOWN (% of capital):")
    print(f"  Mean: {results_df['max_drawdown'].mean():.2f}%")
    print(f"  Median: {results_df['max_drawdown'].median():.2f}%")
    print(f"  Min:  {results_df['max_drawdown'].min():.2f}%")
    print(f"  Max:  {results_df['max_drawdown'].max():.2f}%")
    
    # Win rate distribution
    print(f"\nWIN RATE:")
    print(f"  Original: {original_win_rate:.1f}%")
    print(f"  Mean: {results_df['win_rate'].mean():.1f}%")
    print(f"  Std:  {results_df['win_rate'].std():.1f}%")
    print(f"  Min:  {results_df['win_rate'].min():.1f}%")
    print(f"  Max:  {results_df['win_rate'].max():.1f}%")
    
    # Consecutive losses
    print(f"\nMAX CONSECUTIVE LOSSES:")
    print(f"  Mean: {results_df['max_consecutive_losses'].mean():.1f}")
    print(f"  Max:  {results_df['max_consecutive_losses'].max()}")
    
    # Risk assessment
    negative_returns = (results_df['final_return'] < 0).sum()
    positive_returns = (results_df['final_return'] > 0).sum()
    
    print(f"\nRISK ASSESSMENT:")
    print(f"  Probability of loss: {negative_returns / iterations * 100:.1f}%")
    print(f"  Probability of profit: {positive_returns / iterations * 100:.1f}%")
    
    # Value at Risk (VaR)
    var_95 = np.percentile(results_df['final_return'], 5)
    print(f"  95% Value at Risk (VaR): ${var_95:,.2f}")
    print(f"  (5% chance of losing more than this amount)")
    
    # Final assessment
    print("\n" + "="*80)
    print("FINAL ASSESSMENT")
    print("="*80)
    
    loss_prob = negative_returns / iterations
    avg_dd = results_df['max_drawdown'].mean()
    
    if loss_prob < 0.10:
        print("✅ LOW PROBABILITY OF LOSS - Excellent")
    elif loss_prob < 0.20:
        print("⚠️  MODERATE PROBABILITY OF LOSS - Acceptable")
    else:
        print("❌ HIGH PROBABILITY OF LOSS - Needs improvement")
    
    if avg_dd > -10:
        print(f"✅ EXCELLENT DRAWDOWN CONTROL - Mean: {avg_dd:.1f}%")
    elif avg_dd > -20:
        print(f"⚠️  ACCEPTABLE DRAWDOWN - Mean: {avg_dd:.1f}%")
    else:
        print(f"❌ HIGH DRAWDOWN RISK - Mean: {avg_dd:.1f}%")
    
    if results_df['final_return'].mean() > original_total * 0.8:
        print(f"✅ STRONG EXPECTED RETURN - ${results_df['final_return'].mean():,.2f}")
    
    # Compare original vs Monte Carlo mean
    diff_pct = abs(results_df['final_return'].mean() - original_total) / original_total * 100
    print(f"\nORIGINAL vs MONTE CARLO:")
    print(f"  Original Return: ${original_total:,.2f}")
    print(f"  Monte Carlo Mean: ${results_df['final_return'].mean():,.2f}")
    print(f"  Difference: {diff_pct:.1f}%")
    
    if diff_pct < 10:
        print("  ✓ Results are consistent - strategy is robust")
    else:
        print("  ⚠️  Results vary significantly - strategy may be sensitive to trade sequence")
    
    # Save results
    results_df.to_csv('monte_carlo_results.csv', index=False)
    print(f"\nDetailed results saved to monte_carlo_results.csv")
    
    # Summary statistics
    summary = {
        'Original Return': original_total,
        'Mean Return': results_df['final_return'].mean(),
        'Std Return': results_df['final_return'].std(),
        'Loss Probability': loss_prob * 100,
        'Avg Drawdown': avg_dd,
        'VaR_95': var_95
    }
    
    summary_df = pd.DataFrame([summary])
    summary_df.to_csv('monte_carlo_summary.csv', index=False)
    print(f"Summary saved to monte_carlo_summary.csv")
    
    return results_df

if __name__ == "__main__":
    results = run_monte_carlo_fixed(iterations=100)