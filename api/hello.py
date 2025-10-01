def handler(request):
    """
    Minimal Vercel Python serverless function for testing detection.

    This follows the exact pattern from Vercel's official Python documentation:
    https://vercel.com/docs/functions/serverless-functions/runtimes/python
    """
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": '{"message": "Hello from Vercel Python function!"}',
    }
