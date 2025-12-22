#!/bin/bash

# Configuration
API_URL="http://localhost:9090/identity"
UE_IP="10.60.0.1" # Example UE IP, replace with actual IP from SMF/UPF logs

echo "Testing Northbound API (Mini-NEF)..."
echo "Target URL: $API_URL"
echo "Querying IP: $UE_IP"

# Call the API
RESPONSE=$(curl -s -X GET "$API_URL?ip=$UE_IP")

# Print Response
echo "Response:"
echo "$RESPONSE"

# Simple Validation
if [[ $RESPONSE == *"msisdn"* ]]; then
  echo "✅ Test Passed: MSISDN found in response."
else
  echo "⚠️ Test Warning: MSISDN not found (might be normal if UE is not attached or BSF sync is missing)."
fi

echo ""
echo "Note: To verify with real data:"
echo "1. Run 'docker logs smf' to find a PDU Session Establishment with an assigned IP."
echo "2. Run this script with that IP: ./test_nef.sh <UE_IP>"
