# Array Support in GenHook

GenHook now supports extracting data from arrays in webhook payloads, enabling processing of webhooks that contain multiple items or locations.

## Features

✅ **Automatic Array Detection** - No syntax changes needed  
✅ **Multiple Value Extraction** - Extracts values from all array elements  
✅ **Template-Friendly Output** - Arrays formatted as comma-separated strings  
✅ **Individual Element Access** - Access specific array elements with `[index]` syntax  
✅ **Backwards Compatible** - Existing configurations continue to work  

## How It Works

When GenHook encounters an array during field extraction:

1. **Collects all matching values** from array elements
2. **Formats for templates** as comma-separated strings  
3. **Provides individual access** via array indexing
4. **Handles missing fields** gracefully across array elements

## Example: Gisual Location Webhook

**Input payload:**
```json
{
  "locations": [
    { 
      "search_id": "ticket-24601",
      "asset_type": "cpe"
    },
    {
      "search_id": "ticket-24602", 
      "asset_type": "node"
    },
    {
      "asset_name": "Node PHL013.56",
      "asset_type": "node",
      "asset_status": "down"
    }
  ]
}
```

**Configuration:**
```ini
gisual = locations{search_id},locations{asset_type},locations{asset_name},locations{asset_status}::MAJOR: Gisual Alert - Assets: $locations.asset_name$ | Types: $locations.asset_type$ | Status: $locations.asset_status$ | IDs: $locations.search_id$
```

**Extracted values:**
- `$locations.search_id$` → `"ticket-24601, ticket-24602"`
- `$locations.asset_type$` → `"cpe, node, node"`
- `$locations.asset_name$` → `"Node PHL013.56"` (only element 2 has this)
- `$locations.asset_status$` → `"down"` (only element 2 has this)

**Generated message:**
```
MAJOR: Gisual Alert - Assets: Node PHL013.56 | Types: cpe, node, node | Status: down | IDs: ticket-24601, ticket-24602
```

## Individual Array Element Access

You can also access specific array elements:

**Template variables available:**
- `$locations.search_id[0]$` → `"ticket-24601"`
- `$locations.search_id[1]$` → `"ticket-24602"`  
- `$locations.asset_type[0]$` → `"cpe"`
- `$locations.asset_type[1]$` → `"node"`
- `$locations.asset_type[2]$` → `"node"`

**Example configuration using specific elements:**
```ini
gisual = locations{search_id},locations{asset_type}::Alert for first location: $locations.search_id[0]$ ($locations.asset_type[0]$) and second: $locations.search_id[1]$ ($locations.asset_type[1]$)
```

## Array Behavior Rules

1. **All Values Collected**: When a field exists in multiple array elements, all values are collected
2. **Missing Fields Handled**: If a field doesn't exist in some elements, those are skipped  
3. **Single Values Simplified**: If only one array element has a field, just that value is returned
4. **Empty Arrays**: Return `None`/empty string if no matching fields found

## Real-World Use Cases

### Multiple GitHub Repository Events
```json
{
  "repositories": [
    {"name": "frontend", "language": "JavaScript"},
    {"name": "backend", "language": "Python"},
    {"name": "mobile", "language": "React Native"}
  ]
}
```

**Configuration:**
```ini
github-multi = repositories{name},repositories{language}::GitHub batch update: $repositories.name$ (Languages: $repositories.language$)
```

**Result:**
```
GitHub batch update: frontend, backend, mobile (Languages: JavaScript, Python, React Native)
```

### AWS CloudFormation Stack Events
```json
{
  "resources": [
    {"type": "AWS::EC2::Instance", "status": "CREATE_COMPLETE"},
    {"type": "AWS::S3::Bucket", "status": "CREATE_COMPLETE"},
    {"type": "AWS::RDS::Instance", "status": "CREATE_FAILED"}
  ]
}
```

**Configuration:**
```ini
aws-stack = resources{type},resources{status}::CloudFormation: $resources.type$ → $resources.status$
```

**Result:**
```
CloudFormation: AWS::EC2::Instance, AWS::S3::Bucket, AWS::RDS::Instance → CREATE_COMPLETE, CREATE_COMPLETE, CREATE_FAILED
```

## Backwards Compatibility

**Existing configurations continue to work unchanged:**

```ini
# These still work exactly as before
github = action,repository{name}::GitHub $action$ on $repository.name$
stripe = type,data{object{amount}}::Stripe $type$: $data.object.amount$
```

Array support is automatically applied when arrays are detected in the payload structure.

## Testing Array Support

Use the provided test script to verify array extraction:

```bash
cd /opt/genhook/backend
python3 test_array_support.py
```

This will show you exactly how array fields are extracted and formatted for template substitution.

## Migration from Single-Item Processing

If you were previously handling array-based webhooks by only processing the first element, you can now:

1. **Keep existing config** - It will now process all array elements
2. **Update templates** - Take advantage of comma-separated values
3. **Add individual access** - Use `[index]` syntax for specific elements when needed

**Before (first element only):**
```
MAJOR: Alert - Asset: Node PHL013.56 Status: down
```

**After (all elements):**
```
MAJOR: Alert - Assets: Node PHL013.56 | Types: cpe, node, node | Status: down | IDs: ticket-24601, ticket-24602
```

---

Array support makes GenHook much more powerful for webhooks containing multiple items, locations, resources, or any other array-based data structures.