#!/usr/bin/env python3
"""
Test field extraction with real webhook payloads.
This verifies our extraction engine works with actual webhook data.
"""
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.extractor import FieldExtractor
from examples.sample_webhooks import get_all_sample_webhooks


def test_extraction_with_config():
    """Test extraction using our webhook configurations."""
    extractor = FieldExtractor()
    
    # Our webhook configurations from webhook-config.ini
    webhook_configs = {
        "github": {
            "fields": ["action", "pull_request{title}", "pull_request{user{login}}", "repository{name}"],
            "template": "GitHub $action$ on $repository.name$: \"$pull_request.title$\" by $pull_request.user.login$"
        },
        "stripe": {
            "fields": ["type", "data{object{amount}}", "data{object{currency}}", "data{object{status}}"],
            "template": "Stripe $type$: Payment of $data.object.amount$ $data.object.currency$ status: $data.object.status$"
        },
        "slack": {
            "fields": ["event{type}", "event{user}", "event{text}"],
            "template": "Slack $event.type$ from user $event.user$: \"$event.text$\""
        },
        "aws": {
            "fields": ["detail-type", "source", "region", "detail{instance-id}", "detail{state}"],
            "template": "AWS $detail-type$ from $source$ in $region$: Instance $detail.instance-id$ state: $detail.state$"
        }
    }
    
    # Get sample webhook payloads
    sample_webhooks = get_all_sample_webhooks()
    
    print("🔍 Testing Field Extraction with Real Webhook Data\n")
    
    for webhook_type, payload in sample_webhooks.items():
        if webhook_type in webhook_configs:
            config = webhook_configs[webhook_type]
            
            print(f"📝 Testing {webhook_type.upper()} webhook:")
            print(f"   Fields: {config['fields']}")
            
            # Extract fields
            extracted = extractor.extract_for_template(payload, config['fields'])
            
            print("   Extracted data:")
            for key, value in extracted.items():
                if not key.startswith(webhook_type + "{") and value is not None:  # Show simplified keys
                    print(f"     • {key}: {value}")
            
            # Show what the template would look like
            template = config['template']
            print(f"   Template: {template}")
            
            # Try to show a preview of template substitution
            preview = template
            for key, value in extracted.items():
                if value is not None:
                    preview = preview.replace(f"${key}$", str(value))
            print(f"   Preview: {preview}")
            print()


def test_complex_extraction():
    """Test extraction of complex nested structures."""
    extractor = FieldExtractor()
    
    print("🧪 Testing Complex Extraction Patterns\n")
    
    # Test with GitHub payload
    github_payload = get_all_sample_webhooks()["github"]
    
    complex_patterns = [
        "pull_request{head{ref}}",      # Deep nesting
        "pull_request{user{id}}",       # Nested user ID
        "repository{owner{login}}",     # Repository owner
    ]
    
    print("Testing complex GitHub patterns:")
    extracted = extractor.extract_for_template(github_payload, complex_patterns)
    
    for pattern in complex_patterns:
        simplified = extractor._simplify_pattern(pattern)
        value = extracted.get(simplified)
        print(f"  • {pattern} → {simplified} = {value}")
    
    print()
    
    # Test with array data
    shopify_payload = get_all_sample_webhooks()["shopify"]
    
    array_patterns = [
        "line_items{0}{title}",         # First item title
        "line_items{0}{price}",         # First item price
        "customer{first_name}",         # Customer name
    ]
    
    print("Testing Shopify array patterns:")
    extracted = extractor.extract_for_template(shopify_payload, array_patterns)
    
    for pattern in array_patterns:
        simplified = extractor._simplify_pattern(pattern)
        value = extracted.get(simplified)
        print(f"  • {pattern} → {simplified} = {value}")


def main():
    """Main test function."""
    try:
        test_extraction_with_config()
        test_complex_extraction()
        print("🎉 All field extraction tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()