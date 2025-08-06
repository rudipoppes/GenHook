#!/usr/bin/env python3
"""
Test script for array support in GenHook field extraction.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.extractor import FieldExtractor

# Test payload similar to Gisual webhook
test_payload = {
    "locations": [
        { 
            "longitude": -75.163674,
            "latitude": 39.952398,
            "search_id": "ticket-24601",
            "asset_type": "cpe"
        },
        {
            "thoroughfare": "41 Ford Street",
            "locality": "San Francisco",
            "administrative_area": "CA",
            "postal_code": "94114",
            "country": "US",
            "search_id": "ticket-24602",
            "asset_type": "node"
        },
        {
            "asset_name": "Node PHL013.56",
            "asset_type": "node", 
            "asset_status": "down"
        }
    ],
    "callback_url": "https://example.com/callback"
}

def test_array_extraction():
    """Test array field extraction."""
    print("🧪 Testing Array Support in GenHook Field Extraction")
    print("=" * 60)
    
    extractor = FieldExtractor()
    
    # Test field patterns
    patterns = [
        'locations{search_id}',
        'locations{asset_type}',
        'locations{asset_name}',
        'locations{asset_status}'
    ]
    
    print("📋 Test Payload:")
    print(f"  Locations count: {len(test_payload['locations'])}")
    print(f"  Field patterns: {patterns}")
    print()
    
    # Extract fields
    print("⚡ Extracting fields...")
    extracted = extractor.extract_fields(test_payload, patterns)
    
    print("📊 Raw Extraction Results:")
    for pattern, value in extracted.items():
        print(f"  {pattern}: {value}")
    print()
    
    # Extract for template
    print("🎯 Template-Ready Extraction:")
    template_vars = extractor.extract_for_template(test_payload, patterns)
    
    for key, value in template_vars.items():
        print(f"  ${key}$: {value}")
    print()
    
    # Test template substitution
    template = "MAJOR: Gisual Alert - Assets: $locations.asset_name$ | Types: $locations.asset_type$ | Status: $locations.asset_status$ | IDs: $locations.search_id$"
    
    print("📝 Template Substitution Test:")
    print(f"Template: {template}")
    print()
    
    # Perform substitution
    message = template
    for key, value in template_vars.items():
        if value is not None:
            old_message = message
            message = message.replace(f"${key}$", str(value))
            if old_message != message:
                print(f"  Replaced ${key}$ with '{value}'")
    
    print()
    print("✅ Final Message:")
    print(f"  {message}")
    print()
    
    # Test individual array access
    print("🔢 Individual Array Element Access:")
    for key in template_vars:
        if '[' in key and ']' in key:
            print(f"  ${key}$: {template_vars[key]}")

if __name__ == "__main__":
    test_array_extraction()