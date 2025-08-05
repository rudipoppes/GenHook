"""
Sample webhook payloads for testing GenHook field extraction.
These are real-world examples from various webhook providers.
"""

# GitHub Pull Request Webhook
GITHUB_PULL_REQUEST = {
    "action": "opened",
    "number": 1,
    "pull_request": {
        "id": 1,
        "title": "Update README",
        "body": "This PR updates the README file with new information.",
        "user": {
            "login": "octocat",
            "id": 1,
            "type": "User"
        },
        "head": {
            "ref": "feature-branch",
            "sha": "abc123def456"
        },
        "base": {
            "ref": "main",
            "sha": "def456ghi789"
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

# Stripe Payment Intent Webhook
STRIPE_PAYMENT_INTENT = {
    "id": "evt_1234567890",
    "object": "event",
    "type": "payment_intent.succeeded",
    "data": {
        "object": {
            "id": "pi_1234567890",
            "amount": 2000,
            "currency": "usd",
            "status": "succeeded",
            "customer": "cus_1234567890",
            "payment_method": "pm_1234567890"
        }
    },
    "created": 1641024000
}

# Slack Message Webhook
SLACK_MESSAGE = {
    "token": "verification_token",
    "team_id": "T1234567890",
    "event": {
        "type": "message",
        "channel": "C1234567890",
        "user": "U1234567890",
        "text": "Hello world",
        "ts": "1234567890.123456"
    },
    "type": "event_callback",
    "event_id": "Ev1234567890",
    "event_time": 1234567890
}

# AWS EC2 State Change Webhook
AWS_EC2_STATE_CHANGE = {
    "version": "0",
    "id": "12345678-1234-1234-1234-123456789012",
    "detail-type": "EC2 Instance State-change Notification",
    "source": "aws.ec2",
    "account": "123456789012",
    "time": "2024-01-15T13:12:22Z",
    "region": "us-east-1",
    "detail": {
        "instance-id": "i-1234567890abcdef0",
        "state": "terminated",
        "previous-state": "running"
    },
    "resources": [
        "arn:aws:ec2:us-east-1:123456789012:instance/i-1234567890abcdef0"
    ]
}

# Cisco Meraki Network Alert
MERAKI_DEVICE_ALERT = {
    "version": "0.1",
    "sharedSecret": "secret_key",
    "sentAt": "2024-01-15T13:12:22.123Z",
    "organizationId": "123456",
    "organizationName": "My Organization",
    "networkId": "N_123456789012345678",
    "networkName": "Main Office",
    "alertId": "alert_id_12345",
    "alertType": "Device went down",
    "alertTypeId": "device_down",
    "alertLevel": "warning",
    "occurredAt": "2024-01-15T13:10:00.000Z",
    "alertData": {
        "name": "Office Switch",
        "tags": ["critical", "main-office"],
        "deviceSerial": "Q2XX-XXXX-XXXX",
        "deviceMac": "00:18:0a:xx:xx:xx",
        "deviceType": "switch",
        "deviceModel": "MS220-24P"
    }
}

# Jira Issue Update Webhook
JIRA_ISSUE_UPDATED = {
    "timestamp": 1642249942123,
    "webhookEvent": "jira:issue_updated",
    "issue_event_type_name": "issue_updated",
    "user": {
        "name": "admin",
        "displayName": "Administrator",
        "emailAddress": "admin@company.com"
    },
    "issue": {
        "id": "10001",
        "key": "PROJ-123",
        "fields": {
            "summary": "Fix login bug",
            "status": {
                "name": "In Progress",
                "id": "3"
            },
            "priority": {
                "name": "High",
                "id": "2"
            },
            "assignee": {
                "name": "developer",
                "displayName": "John Developer",
                "emailAddress": "john@company.com"
            }
        }
    },
    "changelog": {
        "id": "12345",
        "items": [
            {
                "field": "status",
                "fieldtype": "jira",
                "from": "1",
                "fromString": "To Do",
                "to": "3",
                "toString": "In Progress"
            }
        ]
    }
}

# Shopify Order Webhook
SHOPIFY_ORDER = {
    "id": 820982911946154508,
    "email": "jon@example.com",
    "created_at": "2024-01-01T10:30:15-05:00",
    "total_price": "25.00",
    "currency": "USD",
    "financial_status": "paid",
    "line_items": [
        {
            "id": 466157049946154508,
            "title": "Product Title",
            "quantity": 1,
            "price": "25.00"
        }
    ],
    "customer": {
        "id": 207119551,
        "email": "jon@example.com",
        "first_name": "Jon",
        "last_name": "Doe"
    }
}

# Azure Event Grid Blob Created
AZURE_BLOB_CREATED = {
    "id": "1807",
    "eventType": "Microsoft.Storage.BlobCreated",
    "subject": "/blobServices/default/containers/test-container/blobs/new-file.txt",
    "eventTime": "2024-01-15T13:12:22.3936312Z",
    "data": {
        "api": "PutBlob",
        "clientRequestId": "6d79dbfb-0e37-4fc4-981f-442c9ca65760",
        "requestId": "831e1650-001e-001b-66ab-eeb76e000000",
        "eTag": "0x8D4BCC2E4835CD0",
        "contentType": "text/plain",
        "contentLength": 524288,
        "blobType": "BlockBlob",
        "url": "https://example.blob.core.windows.net/test-container/new-file.txt",
        "sequencer": "00000000000004420000000000028963"
    },
    "dataVersion": "2",
    "metadataVersion": "1",
    "topic": "/subscriptions/subscription-id/resourceGroups/Storage/providers/Microsoft.Storage/storageAccounts/xstoretestaccount"
}


def get_all_sample_webhooks():
    """Get all sample webhooks for testing."""
    return {
        "github": GITHUB_PULL_REQUEST,
        "stripe": STRIPE_PAYMENT_INTENT,
        "slack": SLACK_MESSAGE,
        "aws": AWS_EC2_STATE_CHANGE,
        "meraki": MERAKI_DEVICE_ALERT,
        "jira": JIRA_ISSUE_UPDATED,
        "shopify": SHOPIFY_ORDER,
        "azure": AZURE_BLOB_CREATED
    }