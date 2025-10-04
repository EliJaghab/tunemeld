"""
Minimal test endpoint to debug Vercel serverless function crashes
"""

from django.http import JsonResponse


def handler(request):
    """Minimal handler to test if basic Django works in Vercel"""
    return JsonResponse({"status": "ok", "message": "Django is working"})
