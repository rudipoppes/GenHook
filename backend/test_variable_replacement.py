#!/usr/bin/env python3
"""
Test script to verify that unresolved variables are replaced with '-'
"""
import re

def test_variable_replacement():
    """Test the regex replacement of unresolved variables"""
    
    test_cases = [
        {
            "name": "Missing ETR and utility",
            "template": "Gisual Alert - Router-Dallas-Core-01 for incident: KEVINDEMO-TDPQ7 for utility $utility$ power on - outage resolved. Est Restore Time: $etr$",
            "replacements": {"incident": "KEVINDEMO-TDPQ7"},  # utility and etr are missing
            "expected": "Gisual Alert - Router-Dallas-Core-01 for incident: KEVINDEMO-TDPQ7 for utility - power on - outage resolved. Est Restore Time: -"
        },
        {
            "name": "GitHub PR with missing reviewer",
            "template": "GitHub PR #$pull_request.number$ by $pull_request.user.login$ - Reviewer: $pull_request.reviewer$",
            "replacements": {"pull_request.number": "123", "pull_request.user.login": "johndoe"},
            "expected": "GitHub PR #123 by johndoe - Reviewer: -"
        },
        {
            "name": "Stripe payment with missing email",
            "template": "Payment of $amount$ from $customer.name$ ($customer.email$) - Status: $status$",
            "replacements": {"amount": "$50.00", "customer.name": "John Smith", "status": "completed"},
            "expected": "Payment of $50.00 from John Smith (-) - Status: completed"
        },
        {
            "name": "AWS alert with multiple missing fields",
            "template": "AWS Alert: Instance $instance.id$ in region $region$ - CPU: $metrics.cpu$%, Memory: $metrics.memory$%",
            "replacements": {"instance.id": "i-1234567", "region": "us-east-1"},
            "expected": "AWS Alert: Instance i-1234567 in region us-east-1 - CPU: -%, Memory: -%"
        },
        {
            "name": "Slack message with empty text",
            "template": "Slack message from $user.name$ in #$channel$: \"$text$\"",
            "replacements": {"user.name": "alice", "channel": "general"},
            "expected": "Slack message from alice in #general: \"-\""
        },
        {
            "name": "All variables resolved",
            "template": "User $name$ logged in from $ip$",
            "replacements": {"name": "admin", "ip": "192.168.1.1"},
            "expected": "User admin logged in from 192.168.1.1"
        }
    ]
    
    print("Testing variable replacement logic...")
    print("=" * 60)
    
    all_passed = True
    
    for test in test_cases:
        print(f"\nTest: {test['name']}")
        print(f"Template: {test['template']}")
        
        # Apply known replacements
        message = test['template']
        for key, value in test['replacements'].items():
            message = message.replace(f"${key}$", str(value))
        
        print(f"After replacements: {message}")
        
        # Replace any remaining unresolved variables with '-'
        # Use a more specific pattern that looks for $word.word$ patterns
        message = re.sub(r'\$[a-zA-Z_][a-zA-Z0-9_.]*\$', '-', message)
        
        print(f"After regex cleanup: {message}")
        print(f"Expected: {test['expected']}")
        
        if message == test['expected']:
            print("✅ PASSED")
        else:
            print("❌ FAILED")
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed")
    
    return all_passed

if __name__ == "__main__":
    test_variable_replacement()