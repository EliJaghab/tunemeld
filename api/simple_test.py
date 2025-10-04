"""
Ultra minimal test endpoint with no Django dependencies
"""


def handler(request):
    """No imports, no dependencies, just pure Python"""
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": '{"status": "ok", "message": "Pure Python works"}',
    }
