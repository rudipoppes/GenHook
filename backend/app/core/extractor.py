"""
JSON field extraction engine for GenHook.
Extracts data from webhook payloads based on configuration patterns.
"""
import re
from typing import Any, Dict, List, Optional, Union


class FieldExtractor:
    """
    Extracts fields from JSON payloads based on patterns.
    
    Supported patterns:
    - Simple field: 'field_name'
    - Nested object: 'object{subfield}'  
    - Deep nesting: 'level1{level2{level3}}'
    - Array access: 'array_field{item_property}' (processes all array items)
    - Array indexing: 'array_field[0]{property}' (specific index)
    """
    
    def __init__(self):
        # Regex pattern to parse field extraction patterns
        # Matches: field_name{subfield{nested}} or simple_field
        self.pattern_regex = re.compile(r'^([^{]+)(?:\{(.+)\})?$')
    
    def extract_fields(self, data: Dict[str, Any], field_patterns: List[str]) -> Dict[str, Any]:
        """
        Extract multiple fields from data based on patterns.
        
        Args:
            data: The JSON webhook payload
            field_patterns: List of extraction patterns like ['action', 'user{name}']
            
        Returns:
            Dictionary mapping pattern to extracted value
        """
        extracted = {}
        
        for pattern in field_patterns:
            try:
                value = self._extract_single_field(data, pattern)
                if value is not None:
                    # Store both the raw pattern and a simplified key
                    extracted[pattern] = value
                    # Also store with simplified key for template variables
                    simplified_key = self._simplify_pattern(pattern)
                    if simplified_key != pattern:
                        extracted[simplified_key] = value
            except Exception as e:
                # Continue processing other fields on error
                extracted[pattern] = None
        
        return extracted
    
    def _extract_single_field(self, data: Dict[str, Any], pattern: str) -> Any:
        """
        Extract a single field based on pattern.
        
        Examples:
        - 'action' -> data['action']
        - 'user{name}' -> data['user']['name']
        - 'data{object}{amount}' -> data['data']['object']['amount']
        """
        if not pattern or not isinstance(data, dict):
            return None
        
        # Parse the pattern with proper brace handling
        field_name, nested_pattern = self._parse_pattern(pattern)
        
        # Get the top-level field
        if field_name not in data:
            return None
        
        current_value = data[field_name]
        
        # If no nesting, return the value
        if not nested_pattern:
            return current_value
        
        # Handle nested extraction recursively
        return self._extract_single_field(current_value, nested_pattern) if isinstance(current_value, dict) else self._extract_nested(current_value, nested_pattern)
    
    def _parse_pattern(self, pattern: str) -> tuple:
        """
        Parse a pattern with proper brace handling.
        
        Examples:
        - 'action' -> ('action', None)
        - 'user{name}' -> ('user', 'name')  
        - 'data{object}{amount}' -> ('data', 'object{amount}')
        """
        if '{' not in pattern:
            return pattern, None
        
        # Find the first opening brace
        brace_start = pattern.find('{')
        field_name = pattern[:brace_start]
        
        # Count braces to find the matching closing brace for the first opening brace
        brace_count = 0
        for i in range(brace_start, len(pattern)):
            if pattern[i] == '{':
                brace_count += 1
            elif pattern[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    # Found the matching closing brace for the first opening brace
                    nested_pattern = pattern[brace_start + 1:i]
                    # If there's more after this closing brace, append it
                    remaining = pattern[i + 1:]
                    if remaining:
                        nested_pattern = nested_pattern + remaining
                    return field_name, nested_pattern if nested_pattern else None
        
        # If we get here, braces don't match
        raise ValueError(f"Unmatched braces in pattern: {pattern}")
    
    def _extract_nested(self, data: Any, pattern: str) -> Any:
        """
        Extract from nested data structure.
        
        Args:
            data: Current data object (dict, list, or primitive)
            pattern: Remaining pattern like 'name' or 'items{0}{title}'
        """
        if not pattern:
            return data
        
        # Parse next level of pattern
        match = self.pattern_regex.match(pattern)
        if not match:
            # Simple field name with no further nesting
            if isinstance(data, dict):
                return data.get(pattern)
            elif isinstance(data, list) and pattern.isdigit():
                index = int(pattern)
                return data[index] if 0 <= index < len(data) else None
            else:
                return None
        
        field_name, remaining_pattern = match.groups()
        field_name = field_name.strip()
        
        # Handle different data types
        if isinstance(data, dict):
            next_value = data.get(field_name)
        elif isinstance(data, list):
            # Handle array access
            if field_name.isdigit():
                index = int(field_name)
                next_value = data[index] if 0 <= index < len(data) else None
            else:
                # Extract field from all array items
                next_value = []
                for item in data:
                    if isinstance(item, dict) and field_name in item:
                        next_value.append(item[field_name])
                
                # If only one item or no items, simplify the result
                if len(next_value) == 0:
                    next_value = None
                elif len(next_value) == 1:
                    next_value = next_value[0]
        else:
            return None
        
        # Continue with remaining pattern
        if remaining_pattern:
            return self._extract_nested(next_value, remaining_pattern)
        else:
            return next_value
    
    def _simplify_pattern(self, pattern: str) -> str:
        """
        Convert extraction pattern to simplified variable name for templates.
        
        Examples:
        - 'user{name}' -> 'user.name'
        - 'pull_request{title}' -> 'pull_request.title'
        - 'pull_request{user{login}}' -> 'pull_request.user.login'
        - 'items{0}{title}' -> 'items.0.title'
        """
        # Replace {field} with .field, handling nested braces
        simplified = pattern
        while '{' in simplified:
            simplified = re.sub(r'\{([^{}]+)\}', r'.\1', simplified)
        return simplified
    
    def extract_for_template(self, data: Dict[str, Any], field_patterns: List[str]) -> Dict[str, Any]:
        """
        Extract fields optimized for template variable substitution.
        
        Returns flattened dictionary with dot notation keys suitable for templates.
        """
        raw_extracted = self.extract_fields(data, field_patterns)
        template_vars = {}
        
        for pattern, value in raw_extracted.items():
            if value is not None:
                # Create template-friendly key
                template_key = self._simplify_pattern(pattern)
                
                # Handle array values for templates
                if isinstance(value, list):
                    # Convert array to string representation for templates
                    template_vars[template_key] = self._format_array_for_template(value)
                    # Also provide individual array elements
                    for i, item in enumerate(value):
                        template_vars[f"{template_key}[{i}]"] = item
                else:
                    template_vars[template_key] = value
                
                # Also support the original pattern key
                template_vars[pattern] = template_vars[template_key]
        
        return template_vars
    
    def _format_array_for_template(self, array_value: List[Any]) -> str:
        """
        Format array values for template substitution.
        
        Examples:
        - ['node', 'cpe'] -> 'node, cpe'
        - ['down', 'active'] -> 'down, active'
        """
        if not array_value:
            return ""
        
        # Convert each item to string and join
        str_items = [str(item) for item in array_value if item is not None]
        return ", ".join(str_items)


class ExtractionError(Exception):
    """Field extraction related errors."""
    pass


# Utility functions for common webhook patterns
def extract_github_data(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Extract common GitHub webhook fields."""
    extractor = FieldExtractor()
    patterns = [
        'action',
        'number',
        'pull_request{title}',
        'pull_request{user{login}}',
        'repository{name}',
        'repository{full_name}',
        'sender{login}'
    ]
    return extractor.extract_for_template(payload, patterns)


def extract_stripe_data(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Extract common Stripe webhook fields."""
    extractor = FieldExtractor()
    patterns = [
        'type',
        'data{object{id}}',
        'data{object{amount}}',
        'data{object{currency}}',
        'data{object{status}}',
        'data{object{customer}}'
    ]
    return extractor.extract_for_template(payload, patterns)


def extract_slack_data(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Extract common Slack webhook fields."""
    extractor = FieldExtractor()
    patterns = [
        'token',
        'team_id',
        'event{type}',
        'event{user}',
        'event{text}',
        'event{channel}',
        'event{ts}'
    ]
    return extractor.extract_for_template(payload, patterns)


def extract_fields(data: Dict[str, Any], field_patterns: List[str]) -> Dict[str, Any]:
    """
    Global function to extract fields from data - for backward compatibility.
    """
    extractor = FieldExtractor()
    return extractor.extract_fields(data, field_patterns)