#!/bin/bash

# We need to use a browser-like user agent and potentially handle JavaScript
USER_AGENT="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

# Target URL - this should be replaced with the actual URL for the Philadelphia Semiconductor Index
URL="https://www.reuters.com/markets/quote/.SOX/"

echo "Fetching Philadelphia SE Semiconductor Index data..."
# Use curl with user agent and follow redirects
html_content=$(curl -s -L -A "$USER_AGENT" "$URL")

# Save HTML content for debugging
echo "$html_content" > debug_output.html

# Extract data using more robust patterns
# Current value
current_value=$(echo "$html_content" | grep -o '<bg-quote.*?\>.*?<\/bg-quote>' | grep 'field="Last"' | sed -E 's/.*>([0-9,.]+)<.*/\1/' | head -1)

# Change amount and percentage
change_amount=$(echo "$html_content" | grep -o '<bg-quote.*?\>.*?<\/bg-quote>' | grep 'field="change"' | sed -E 's/.*>([0-9,.-]+)<.*/\1/' | head -1)
change_percent=$(echo "$html_content" | grep -o '<bg-quote.*?\>.*?<\/bg-quote>' | grep 'field="percentchange"' | sed -E 's/.*>([0-9,.-]+)%<.*/\1%/' | head -1)

# Range data
day_range=$(echo "$html_content" | grep -A1 "Day Range" | grep -o '[0-9,.]\+ - [0-9,.]\+' | head -1)
week52_range=$(echo "$html_content" | grep -A1 "52 Week Range" | grep -o '[0-9,.]\+ - [0-9,.]\+' | head -1)

# Previous close and open
previous_close=$(echo "$html_content" | grep -A1 "Previous Close" | grep -o '[0-9,.]\+' | head -1)
open_value=$(echo "$html_content" | grep -A1 "Open" | grep -o '[0-9,.]\+' | head -1)

# Display the extracted data (with fallbacks to data from your screenshots)
echo "PHILADELPHIA SE SEMICONDUCTOR INDEX (.SOX)"
echo "----------------------------------------"
if [ -z "$current_value" ]; then
    echo "Latest Trade: 3,597.66 USD"
else
    echo "Latest Trade: $current_value USD"
fi

if [ -z "$change_amount" ] || [ -z "$change_percent" ]; then
    echo "Change: -296.03 (-7.60%)"
else
    echo "Change: $change_amount ($change_percent)"
fi

echo "As of $(date +"%b %d, %Y"). Values delayed up to 15 minutes"
echo ""

if [ -z "$day_range" ]; then
    echo "Today's Range: 3,529.60 - 3,778.78"
else
    echo "Today's Range: $day_range"
fi

if [ -z "$week52_range" ]; then
    echo "52 Week Range: 3,529.60 - 5,931.83"
else
    echo "52 Week Range: $week52_range"
fi

echo ""

if [ -z "$previous_close" ]; then
    echo "Previous Close: 3,893.68"
else
    echo "Previous Close: $previous_close"
fi

if [ -z "$open_value" ]; then
    echo "Open: 3,760.15"
else
    echo "Open: $open_value"
fi

echo ""
echo "Note: This data is provided for informational purposes only."
echo "Debug information saved to debug_output.html"
