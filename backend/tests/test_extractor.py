"""
Tests for the field extraction engine.
"""
import unittest
from app.core.extractor import FieldExtractor, extract_github_data


class TestFieldExtractor(unittest.TestCase):
    """Test field extraction functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.extractor = FieldExtractor()
        
        # Sample GitHub webhook payload
        self.github_payload = {
            "action": "opened",
            "number": 42,
            "pull_request": {
                "id": 123456789,
                "title": "Fix login bug",
                "user": {
                    "login": "octocat",
                    "id": 1,
                    "type": "User"
                },
                "head": {
                    "ref": "feature-branch",
                    "sha": "abc123"
                }
            },
            "repository": {
                "name": "Hello-World",
                "full_name": "octocat/Hello-World",
                "owner": {
                    "login": "octocat"
                }
            },
            "sender": {
                "login": "octocat"
            }
        }
        
        # Sample Stripe webhook payload
        self.stripe_payload = {
            "id": "evt_123456789",
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": "pi_123456789",
                    "amount": 2000,
                    "currency": "usd",
                    "status": "succeeded",
                    "customer": "cus_123456789"
                }
            },
            "created": 1234567890
        }
        
        # Sample array data
        self.array_payload = {
            "items": [
                {"id": 1, "title": "First Item", "price": 10.00},
                {"id": 2, "title": "Second Item", "price": 20.00}
            ],
            "total": 30.00
        }
    
    def test_simple_field_extraction(self):
        """Test extracting simple top-level fields."""
        patterns = ["action", "number"]
        result = self.extractor.extract_fields(self.github_payload, patterns)
        
        self.assertEqual(result["action"], "opened")
        self.assertEqual(result["number"], 42)
    
    def test_nested_field_extraction(self):
        """Test extracting nested fields."""
        patterns = ["pull_request{title}", "pull_request{user{login}}"]
        result = self.extractor.extract_fields(self.github_payload, patterns)
        
        self.assertEqual(result["pull_request{title}"], "Fix login bug")
        self.assertEqual(result["pull_request{user{login}}"], "octocat")
    
    def test_deep_nesting(self):
        """Test extracting deeply nested fields."""
        patterns = ["repository{owner{login}}"]
        result = self.extractor.extract_fields(self.github_payload, patterns)
        
        self.assertEqual(result["repository{owner{login}}"], "octocat")
    
    def test_array_access(self):
        """Test extracting from arrays."""
        patterns = ["items{0}{title}", "items{1}{price}"]
        result = self.extractor.extract_fields(self.array_payload, patterns)
        
        self.assertEqual(result["items{0}{title}"], "First Item")
        self.assertEqual(result["items{1}{price}"], 20.00)
    
    def test_missing_fields(self):
        """Test handling of missing fields."""
        patterns = ["nonexistent", "pull_request{missing}", "missing{nested{field}}"]
        result = self.extractor.extract_fields(self.github_payload, patterns)
        
        self.assertIsNone(result.get("nonexistent"))
        self.assertIsNone(result.get("pull_request{missing}"))
        self.assertIsNone(result.get("missing{nested{field}}"))
    
    def test_template_variable_generation(self):
        """Test generation of template-friendly variable names."""
        patterns = ["pull_request{title}", "pull_request{user{login}}"]
        result = self.extractor.extract_for_template(self.github_payload, patterns)
        
        # Should have both original pattern and simplified key
        self.assertEqual(result["pull_request{title}"], "Fix login bug")
        self.assertEqual(result["pull_request.title"], "Fix login bug")
        self.assertEqual(result["pull_request{user{login}}"], "octocat")
        self.assertEqual(result["pull_request.user.login"], "octocat")
    
    def test_stripe_extraction(self):
        """Test Stripe-specific field extraction."""
        patterns = ["type", "data{object{amount}}", "data{object{currency}}"]
        result = self.extractor.extract_fields(self.stripe_payload, patterns)
        
        self.assertEqual(result["type"], "payment_intent.succeeded")
        self.assertEqual(result["data{object{amount}}"], 2000)
        self.assertEqual(result["data{object{currency}}"], "usd")
    
    def test_pattern_simplification(self):
        """Test pattern simplification for template variables."""
        test_cases = [
            ("action", "action"),
            ("user{name}", "user.name"),
            ("pull_request{user{login}}", "pull_request.user.login"),
            ("items{0}{title}", "items.0.title"),
            ("data{object{amount}}", "data.object.amount")
        ]
        
        for pattern, expected in test_cases:
            simplified = self.extractor._simplify_pattern(pattern)
            self.assertEqual(simplified, expected, f"Pattern '{pattern}' should simplify to '{expected}', got '{simplified}'")
    
    def test_github_helper_function(self):
        """Test the GitHub extraction helper function."""
        result = extract_github_data(self.github_payload)
        
        # Should extract common GitHub fields
        self.assertEqual(result.get("action"), "opened")
        self.assertEqual(result.get("pull_request.title"), "Fix login bug")
        self.assertEqual(result.get("pull_request.user.login"), "octocat")
        self.assertEqual(result.get("repository.name"), "Hello-World")
    
    def test_invalid_patterns(self):
        """Test handling of invalid extraction patterns."""
        # Should handle gracefully without crashing
        patterns = ["", "invalid{", "{missing_start"]
        result = self.extractor.extract_fields(self.github_payload, patterns)
        
        # Should not crash, but values should be None
        self.assertIsNone(result.get(""))
    
    def test_array_field_search(self):
        """Test searching for fields across array items."""
        payload = {
            "users": [
                {"name": "Alice", "role": "admin"},
                {"name": "Bob", "role": "user"},
                {"name": "Charlie", "role": "user"}
            ]
        }
        
        patterns = ["users{name}", "users{role}"]
        result = self.extractor.extract_fields(payload, patterns)
        
        # Should find first matching field in array
        self.assertEqual(result["users{name}"], "Alice")
        self.assertEqual(result["users{role}"], "admin")


if __name__ == '__main__':
    unittest.main()