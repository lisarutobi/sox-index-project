#!/bin/bash

# Strict mode
set -euo pipefail

# Configuration
DATA_DIR="/home/ubuntu/sox-index-project/data"
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")

# Fetch webpage
fetch_webpage() {
    curl -s -L -v "https://indexes.nasdaqomx.com/index/Overview/SOX" \
        -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)" 2> "$DATA_DIR/curl_debug.log"
}

# Advanced regex-based extraction
extract_data() {
    local webpage="$1"
    
    # Regex patterns for extraction (more flexible with whitespace)
    last_price_regex='<td[^>]*>Last</td>\s*<td[^>]*>\s*([0-9,.]+)\s*</td>'
    net_change_regex='<td[^>]*>Net Change</td>\s*<td[^>]*>\s*(-?[0-9,.]+)\s*</td>'
    day_high_regex='<td[^>]*>Day High</td>\s*<td[^>]*>\s*([0-9,.]+)\s*</td>'
    
    # Extract using regex
    if [[ $webpage =~ $last_price_regex ]]; then
        LAST_PRICE="${BASH_REMATCH[1]//,/}"  # Remove commas
    else
        LAST_PRICE="N/A"
    fi
    
    if [[ $webpage =~ $net_change_regex ]]; then
        NET_CHANGE="${BASH_REMATCH[1]//,/}"  # Remove commas
    else
        NET_CHANGE="N/A"
    fi
    
    if [[ $webpage =~ $day_high_regex ]]; then
        DAY_HIGH="${BASH_REMATCH[1]//,/}"  # Remove commas
    else
        DAY_HIGH="N/A"
    fi
}

# Log data to CSV
log_data() {
    mkdir -p "$DATA_DIR/historical"
    echo "$TIMESTAMP,$LAST_PRICE,$NET_CHANGE,$DAY_HIGH" >> "$DATA_DIR/historical/sox_index_$(date +"%Y%m%d").csv"
    FILE="$DATA_DIR/historical/sox_index_$(date +"%Y%m%d").csv"
    LINE_COUNT=$(wc -l < "$FILE")
    if (( LINE_COUNT < 2 )); then
      echo "Warning: CSV for today has only $LINE_COUNT row(s)." >> "$DATA_DIR/scrape_warnings.log"
    fi
}

# Main scraping function
main() {
    local webpage
    webpage=$(fetch_webpage)
    # Save the webpage to a file for debugging
    echo "$webpage" > "$DATA_DIR/debug_webpage.html"
    extract_data "$webpage"
    log_data
    
    # Optional: print to console
    echo "Timestamp: $TIMESTAMP"
    echo "Last Price: $LAST_PRICE"
    echo "Net Change: $NET_CHANGE"
    echo "Day High: $DAY_HIGH"
    if [[ "$LAST_PRICE" == "N/A" || "$NET_CHANGE" == "N/A" ]]; then
        echo "ERROR $(date): Failed to extract data" >> "$DATA_DIR/scrape_errors.log"
        # Send notification or alert here
    fi
}

# Execute main function
main
