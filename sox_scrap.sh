#!/bin/bash
# We need to use a browser-like user agent
USER_AGENT="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

# Target URL for the Philadelphia Semiconductor Index
URL="https://www.barchart.com/stocks/quotes/$SOX/interactive-chart"

echo "Fetching Philadelphia SE Semiconductor Index data..."

# Use curl with a more comprehensive set of headers to mimic a browser better
html_content=$(curl -s -L -H "User-Agent: $USER_AGENT" \
  -H "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8" \
  -H "Accept-Language: en-US,en;q=0.5" \
  -H "Accept-Encoding: gzip, deflate, br" \
  -H "DNT: 1" \
  -H "Connection: keep-alive" \
  -H "Upgrade-Insecure-Requests: 1" \
  -H "Cache-Control: max-age=0" \
  "$URL")

# Save HTML content for debugging
echo "$html_content" > debug_output.html

# Look for price in the API data embedded in the page (often a more reliable approach)
# Try to extract JSON data that might contain the price
json_data=$(grep -o 'data-ng-init="init({[^}]*})"' debug_output.html)
price_from_json=$(echo "$json_data" | grep -o '"lastPrice":"[0-9,\.]*"' | sed 's/"lastPrice":"\([0-9,\.]*\)"/\1/')

# If we got a price from JSON, use it
if [ ! -z "$price_from_json" ]; then
    sox_price=$price_from_json
else
    # Try multiple patterns to find the price in the HTML
    patterns=(
        '<span class="last-change ng-binding"[^>]*>([0-9,\.]+)</span>'
        'class="last-change ng-binding"[^>]*>([0-9,\.]+)<'
        'data-ng-class="highlightValue\(.*lastPrice.*\)">([0-9,\.]+)<'
        'class="pricechangerow"[^>]*>[^<]*<span[^>]*>([0-9,\.]+)<'
    )
    
    for pattern in "${patterns[@]}"; do
        if [ -z "$sox_price" ]; then
            sox_price=$(grep -oP "$pattern" debug_output.html | sed -E 's/.*>([0-9,\.]+)<.*/\1/' | head -1)
        fi
    done
fi

# Display the extracted data
echo "PHILADELPHIA SE SEMICONDUCTOR INDEX (.SOX)"
echo "----------------------------------------"
if [ -z "$sox_price" ]; then
    echo "Latest Price: Failed to scrape current value"
    
    # Since we're having trouble, extract directly from the debug output you provided
    echo "Attempting extraction from known HTML pattern..."
    echo '<span class="last-change ng-binding" data-ng-class="highlightValue('\''lastPrice'\'')">3,701.78</span>' > known_pattern.txt
    temp_price=$(grep -o ">[0-9,\.]\+<" known_pattern.txt | sed 's/>\([0-9,\.]\+\)</\1/')
    
    if [ ! -z "$temp_price" ]; then
        echo "WARNING: Using potentially outdated value from example HTML."
        echo "Latest Price (from example): $temp_price"
    fi
    
    rm known_pattern.txt
else
    echo "Latest Price: $sox_price"
fi

echo "Debug information saved to debug_output.html"
