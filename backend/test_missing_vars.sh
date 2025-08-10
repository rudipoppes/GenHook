#!/bin/bash

# Test the variable replacement with a gisual webhook that has missing fields

echo "Testing gisual webhook with missing utility and etr fields..."
echo "-----------------------------------------------------------"

# First, check if gisual is configured
echo "Checking webhook config for gisual..."
grep "^gisual:" config/webhook-config.ini

echo -e "\n\nSending test webhook with missing fields..."

# Send a webhook with missing utility and etr fields
curl -X POST http://localhost:8000/webhook/gisual \
  -H "Content-Type: application/json" \
  -d '{
    "incident": "KEVINDEMO-TDPQ7",
    "device": "Router-Dallas-Core-01",
    "status": "power on - outage resolved"
  }' | python3 -m json.tool

echo -e "\n\nDone!"