#!/usr/bin/env python3

import subprocess
import csv
import os
import datetime
import re
from pytz import timezone  # Import pytz for timezone handling

def is_market_open():
    """Check if current time is within NASDAQ trading hours (9:30 AM - 4:00 PM ET, Mon-Fri)"""
    # Get current time in Eastern Time (ET)
    eastern = timezone('US/Eastern')
    current_time = datetime.datetime.now(eastern)
    
    # Define market hours (9:30 AM to 4:00 PM ET)
    market_open = datetime.time(9, 30)   # 9:30 AM
    market_close = datetime.time(16, 0)  # 4:00 PM
    
    # Check if it's a weekday (Monday=0, Sunday=6)
    if current_time.weekday() >= 5:  # Saturday or Sunday
        return False
    
    # Check if current time is within trading hours
    current_time_only = current_time.time()
    return market_open <= current_time_only <= market_close

def run_bash_script():
    """Run the bash script and capture its output"""
    try:
        result = subprocess.run(['./sox_scrap.sh'], capture_output=True, text=True)
        return result.stdout
    except Exception as e:
        print(f"Error running bash script: {e}")
        return None

def parse_bash_output(output):
    """Parse the output from the bash script to extract relevant data"""
    data = {
        'date': datetime.datetime.now().strftime('%Y-%m-%d'),
        'time': datetime.datetime.now().strftime('%H:%M:%S')
    }

    patterns = {
        'current_value': r'Latest Trade: ([0-9,.]+) USD',
        'change_amount': r'Change: ([^(]+)',
        'change_percent': r'\(([-0-9,.]+)%\)',
        'day_range': r"Today's Range: ([0-9,.]+) - ([0-9,.]+)",
        'week52_range': r'52 Week Range: ([0-9,.]+) - ([0-9,.]+)',
        'previous_close': r'Previous Close: ([0-9,.]+)',
        'open_value': r'Open: ([0-9,.]+)'
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, output)
        if match:
            if key == 'day_range':
                data['day_low'] = float(match.group(1).replace(',', ''))
                data['day_high'] = float(match.group(2).replace(',', ''))
            elif key == 'week52_range':
                data['week52_low'] = float(match.group(1).replace(',', ''))
                data['week52_high'] = float(match.group(2).replace(',', ''))
            elif key == 'change_amount':
                amount = match.group(1).strip()
                if amount.startswith('-'):
                    data[key] = float(amount.replace(',', ''))
                else:
                    data[key] = float(amount.replace(',', ''))
            elif key == 'change_percent':
                data[key] = float(match.group(1).replace(',', ''))
            else:
                data[key] = float(match.group(1).replace(',', ''))

    return data

def save_to_csv(data, csv_path='sox_index_data.csv'):
    """Save the extracted data to a CSV file"""
    fieldnames = [
        'date', 'time', 'current_value', 'change_amount', 'change_percent',
        'day_low', 'day_high', 'week52_low', 'week52_high',
        'previous_close', 'open_value'
    ]

    file_exists = os.path.isfile(csv_path)

    with open(csv_path, 'a', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        writer.writerow(data)

    print(f"Data saved to {csv_path}")

def main():
    print("Checking if market is open...")
    if not is_market_open():
        print("Market is closed. Skipping data collection.")
        return

    print("Running bash script to fetch Philadelphia SE Semiconductor Index data...")
    bash_output = run_bash_script()

    if bash_output:
        data = parse_bash_output(bash_output)
        save_to_csv(data)
        print(f"Successfully extracted and saved data for {data['date']} at {data['time']}")
        print(f"Current value: {data['current_value']:.2f} USD, Change: {data['change_amount']:.2f} ({data['change_percent']:.2f}%)")
    else:
        print("Failed to get data from bash script")

if __name__ == "__main__":
    main()
