import pandas as pd

LOG_FILE = "trade_log.csv"


def calculate_max_drawdown(equity_series: pd.Series) -> float:
    running_peak = equity_series.cummax()
    drawdown = equity_series - running_peak
    return float(drawdown.min())


def print_summary():
    try:
        df = pd.read_csv(LOG_FILE)
    except FileNotFoundError:
        print("No trade log found yet.")
        return

    if df.empty:
        print("Trade log is empty.")
        return

    total_trades = len(df)
    gross_pnl = df["gross_pnl"].sum() if "gross_pnl" in df.columns else df["pnl"].sum()
    total_commissions = df["commission"].sum() if "commission" in df.columns else 0.0
    net_pnl = df["pnl"].sum()
    win_rate = (df["pnl"] > 0).mean() * 100
    avg_pnl = df["pnl"].mean()
    max_drawdown = calculate_max_drawdown(df["equity"])

    print("\n===== SUMMARY STATS =====")
    print(f"Total trades: {total_trades}")
    print(f"Gross PnL: {gross_pnl:.2f}")
    print(f"Total commissions: {total_commissions:.2f}")
    print(f"Net PnL: {net_pnl:.2f}")
    print(f"Win rate: {win_rate:.2f}%")
    print(f"Average PnL per trade: {avg_pnl:.2f}")
    print(f"Max drawdown: {max_drawdown:.2f}")

    print("\n===== PnL BY STRATEGY =====")
    grouped = df.groupby("strategy")["pnl"].agg(["count", "sum", "mean"])
    print(grouped)

    print("\n===== LAST 5 TRADES =====")
    print(df.tail(5))