#!/bin/bash

# Clear existing crontab
crontab -r 2>/dev/null || true

# Add new cron jobs
(crontab -l 2>/dev/null; echo "*/5 * * * * /home/ubuntu/sox-index-project/test_collector.py") | crontab - || { echo "Failed to set scraping cron job"; exit 1; }
(crontab -l 2>/dev/null; echo "0 20 * * * /usr/bin/python3 /home/ubuntu/sox-index-project/test_dashboard.py") | crontab - || { echo "Failed to set daily report cron job"; exit 1; }

echo "Cron jobs set successfully"#!/bin/bash

