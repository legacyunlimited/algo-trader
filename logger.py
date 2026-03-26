import csv
import os
from datetime import datetime

LOG_FILE = "trade_log.csv"

def init_log():
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([
                "timestamp", "strategy", "signal", "risk", 
                "gross_pnl", "commission", "pnl", "equity", "daily_pnl"
            ])

def log_trade(timestamp, strategy, signal, risk, gross_pnl, commission, pnl, equity, daily_pnl):
    if isinstance(timestamp, str):
        try:
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except:
            timestamp = datetime.now()
    elif not isinstance(timestamp, datetime):
        timestamp = datetime.now()
    
    timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
    
    with open(LOG_FILE, mode="a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([
            timestamp_str, strategy, signal, round(risk, 2),
            round(gross_pnl, 2), round(commission, 2), round(pnl, 2),
            round(equity, 2), round(daily_pnl, 2)
        ])
