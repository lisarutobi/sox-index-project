#!/bin/bash
# Direct SOX data fetcher using identified API

# Try different known API endpoints for SOX data
DATA_DIR="$(dirname "$0")"
OUTPUT_FILE="$DATA_DIR/latest_sox_data.json"

# Array of potential API endpoints from our analysis
declare -a ENDPOINTS=(
    "https://indexes.nasdaqomx.com/Index/Symbol/SOX"
    "https://api.nasdaq.com/api/quote/SOX/info"
    "https://api.nasdaq.com/api/quote/SOX/chart"
    "https://api.nasdaq.com/api/quote/SOX/summary"
    "https://indexes.nasdaqomx.com/api/data/SOX"
)

# Try each endpoint until we get useful data
for endpoint in "${ENDPOINTS[@]}"; do
    echo "Trying endpoint: $endpoint"
    
    curl -s -H "User-Agent: Mozilla/5.0" \
         -H "Accept: application/json" \
         -H "Referer: https://indexes.nasdaqomx.com/" \
         "$endpoint" > "$OUTPUT_FILE"
    
    # Check if we got valid JSON and it has useful data
    if jq . "$OUTPUT_FILE" >/dev/null 2>&1; then
        if grep -q "SOX\|price\|value\|index" "$OUTPUT_FILE"; then
            echo "✓ Found valid data!"
            jq . "$OUTPUT_FILE" > "$DATA_DIR/formatted_sox_data.json"
            
            # Try to extract the key values
            echo "Last Price: $(jq -r '.price // .lastSalePrice // .value // .lastPrice // "Not found"' "$OUTPUT_FILE")"
            echo "Net Change: $(jq -r '.priceChange // .netChange // .change // "Not found"' "$OUTPUT_FILE")"
            echo "Percent Change: $(jq -r '.percentageChange // .percentChange // .changePercent // "Not found"' "$OUTPUT_FILE")"
            
            exit 0
        else
            echo "✗ Valid JSON but no useful data"
        fi
    else
        echo "✗ Invalid JSON response"
    fi
done

echo "Could not find working API endpoint"
exit 1
