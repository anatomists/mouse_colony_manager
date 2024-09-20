import logging
from django.http import JsonResponse

logger = logging.getLogger(__name__)


class CustomExceptionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        logger.exception(f"Unhandled exception: {str(exception)}")

        return JsonResponse({
            'error': 'An unexpected error occurred',
            'detail': str(exception),
            'status': 500
        }, status=500)
