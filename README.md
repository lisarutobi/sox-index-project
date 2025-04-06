#SOX dashboard
A tool to scrape and visualize the Philadelphia SE Semiconductor Index (.SOX) in real-time.

Features
- Bash-based scraping
- Real-time dashboard
- Historical data in CSV
- Daily updates

Tech Stack
- Bash
- Python Dash
- Regex
- Cron

Workflow
Scrape: sox_scrap.py fetches .SOX data (e.g., Latest Trade: 3,597.66 USD, Change: -7.60%).
Collect: sox_collector.py saves data to sox_index_data.csv.
Display: sox_dashboard.py hosts a dashboard at 141.253.119.200.

Setup
Clone: git clone <repo-url>
Setup venv: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt
Run: bash sox_scrap.py && python sox_collector.py && python sox_dashboard.py
Automate: Use Cron for scheduling, Supervisor for dashboard (sudo supervisorctl restart sox_dashboard).# SOX Index Monitoring Dashboard

