from django.views import View
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import time
import logging
from django.http import JsonResponse
from dataclasses import asdict

from .services.text_moderation import TextModerationService

# Create your views here.
class HomeView(View):
    def get(self, request, *args, **kwargs):
        return JsonResponse({'message': 'Hello, World!'})


class ModerateText(APIView):
    def __init__(self):
        super().__init__()
        self.moderation_service = TextModerationService()
        self.logger = logging.getLogger(__name__)

    def post(self, request, *args, **kwargs):
        start_time = time.time()
        
        try:
            # Validate request
            is_valid, error_message = self.moderation_service.validate_request(request.data)
            if not is_valid:
                return Response(
                    {"status": "ERROR", "message": error_message},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Extract data
            text_content = request.data['content']['text']
            config = request.data.get('configuration', {})
            categories = self.moderation_service.validate_categories(config.get('categories'))
            
            # Process text moderation
            moderation_result = self.moderation_service.moderate_text(text_content)
            
            # Calculate processing time
            processing_time = int((time.time() - start_time) * 1000)
            
            # Format and return response
            response_data = self.moderation_service.format_response(
                asdict(moderation_result),
                request.data,
                processing_time
            )
            
            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            self.logger.error(f"Error processing moderation request: {str(e)}")
            return Response(
                {
                    "status": "ERROR",
                    "message": "An error occurred while processing the request",
                    "error": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
