# File: /home/ubuntu/sox-index-project/dashboard/daily_report.py

import pandas as pd
from datetime import datetime
import os

def load_today_data():
    today = datetime.now().strftime("%Y%m%d")
    filepath = f"/home/ubuntu/sox-index-project/data/historical/sox_index_{today}.csv"
    if not os.path.exists(filepath):
        print("No data collected for today.")
        return pd.DataFrame(columns=['timestamp', 'last_price', 'net_change', 'day_high'])
    
    df = pd.read_csv(filepath, header=None, names=['timestamp', 'last_price', 'net_change', 'day_high'])
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

def generate_report(df):
    if df.empty:
        return "No data available for today."

    report = {
        'Date': datetime.now().date().isoformat(),
        'Open Price': float(df['last_price'].iloc[0]),
        'Close Price': float(df['last_price'].iloc[-1]),
        'Max Price': float(df['last_price'].max()),
        'Min Price': float(df['last_price'].min()),
        'Total Net Change': float(df['net_change'].sum()),
        'Data Points': int(len(df))
    }

    return report

def save_report(report):
    output_path = "/home/ubuntu/sox-index-project/data/daily_report.log"
    with open(output_path, 'a') as f:
        f.write(f"--- Daily Report ({report['Date']}) ---\n")
        for key, value in report.items():
            f.write(f"{key}: {value}\n")
        f.write("\n")

def main():
    df = load_today_data()
    report = generate_report(df)
    
    if isinstance(report, str):  # Handle "no data" case
        print(report)
    else:
        save_report(report)
        print("Daily report saved.")

if __name__ == '__main__':
    main()
