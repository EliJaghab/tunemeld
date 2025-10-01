"""Extremely simple test function to verify basic Python runtime."""


def handler(request):
    """Test basic Python functionality without any imports."""
    try:
        # Test basic Python operations
        result = {"status": "success", "python_working": True}
        return f"Basic Python test successful: {result}"
    except Exception as e:
        return f"Basic Python test failed: {e!s}"
