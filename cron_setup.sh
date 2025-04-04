#!/bin/bash

# Scraping every 5 minutes
(crontab -l 2>/dev/null; echo "*/5 * * * * /home/ubuntu/sox-index-project/scraper/scrape_sox.sh") | crontab -

# Daily report at 8 PM
(crontab -l 2>/dev/null; echo "0 20 * * * /usr/bin/python3 /home/ubuntu/sox-index-project/dashboard/daily_report.py") | crontab -
