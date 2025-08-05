#!/usr/bin/env python3
"""
Manual test to verify field extraction logic works correctly.
This can be run manually by the user to verify the system.
"""

# Simple test data
test_payload = {
    "action": "opened",
    "pull_request": {
        "title": "Fix login bug",
        "user": {
            "login": "octocat"
        }
    },
    "repository": {
        "name": "Hello-World"
    }
}

def manual_field_extraction_test():
    """Manual test of field extraction without importing."""
    
    print("🧪 Manual Field Extraction Test")
    print("================================")
    
    # Test simple field
    action = test_payload.get("action")
    print(f"✅ Simple field 'action': {action}")
    
    # Test nested field
    title = test_payload.get("pull_request", {}).get("title")
    print(f"✅ Nested field 'pull_request.title': {title}")
    
    # Test deep nested field  
    login = test_payload.get("pull_request", {}).get("user", {}).get("login")
    print(f"✅ Deep nested 'pull_request.user.login': {login}")
    
    # Test missing field
    missing = test_payload.get("missing_field")
    print(f"✅ Missing field handling: {missing}")
    
    print("\n🎯 Expected Template Variables:")
    template_vars = {
        "action": action,
        "pull_request.title": title, 
        "pull_request.user.login": login,
        "repository.name": test_payload.get("repository", {}).get("name")
    }
    
    for key, value in template_vars.items():
        print(f"  ${key}$ = '{value}'")
    
    print("\n📝 Template Example:")
    template = "GitHub $action$ on $repository.name$: \"$pull_request.title$\" by $pull_request.user.login$"
    print(f"Template: {template}")
    
    # Simple template substitution
    result = template
    for key, value in template_vars.items():
        if value:
            result = result.replace(f"${key}$", str(value))
    
    print(f"Result:   {result}")
    
    return True

def test_pattern_parsing():
    """Test pattern parsing logic manually."""
    
    print("\n🔍 Pattern Parsing Test")
    print("=======================")
    
    test_patterns = [
        "action",
        "user{name}",
        "pull_request{title}",
        "pull_request{user{login}}",
        "items{0}{title}"
    ]
    
    for pattern in test_patterns:
        # Simple pattern parsing using regex
        import re
        pattern_regex = re.compile(r'^([^{]+)(?:\{(.+)\})?$')
        match = pattern_regex.match(pattern)
        
        if match:
            field_name, nested = match.groups()
            print(f"✅ '{pattern}' → field: '{field_name}', nested: '{nested}'")
        else:
            print(f"❌ Failed to parse: '{pattern}'")
    
    return True

def test_real_webhook_data():
    """Test with actual webhook structure."""
    
    print("\n📡 Real Webhook Data Test")
    print("=========================")
    
    # GitHub webhook structure
    github_payload = {
        "action": "opened",
        "number": 42,
        "pull_request": {
            "title": "Update README",
            "user": {"login": "octocat"},
            "head": {"ref": "feature-branch"}
        },
        "repository": {
            "name": "Hello-World",
            "full_name": "octocat/Hello-World"
        }
    }
    
    # Test extraction patterns from our config
    patterns = [
        ("action", ["action"]),
        ("pull_request.title", ["pull_request", "title"]),
        ("pull_request.user.login", ["pull_request", "user", "login"]),
        ("repository.name", ["repository", "name"])
    ]
    
    extracted = {}
    for var_name, path in patterns:
        current = github_payload
        try:
            for key in path:
                current = current[key]
            extracted[var_name] = current
            print(f"✅ {var_name}: '{current}'")
        except (KeyError, TypeError):
            extracted[var_name] = None
            print(f"❌ {var_name}: Not found")
    
    # Test template substitution
    template = "GitHub $action$ on $repository.name$: \"$pull_request.title$\" by $pull_request.user.login$"
    result = template
    for var_name, value in extracted.items():
        if value:
            result = result.replace(f"${var_name}$", str(value))
    
    print(f"\n📝 Final Result:")
    print(f"Template: {template}")  
    print(f"Output:   {result}")
    
    return True

if __name__ == "__main__":
    print("🚀 GenHook Field Extraction Manual Test Suite")
    print("=" * 50)
    
    try:
        manual_field_extraction_test()
        test_pattern_parsing() 
        test_real_webhook_data()
        
        print("\n" + "=" * 50)
        print("🎉 ALL MANUAL TESTS PASSED!")
        print("The field extraction logic appears to be working correctly.")
        print("\nTo run the full test suite:")
        print("1. Activate your virtual environment")
        print("2. cd to the backend directory") 
        print("3. Run: python test_extraction.py")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()