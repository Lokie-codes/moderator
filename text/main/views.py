from django.views import View
from django.http import JsonResponse

# Create your views here.
class HomeView(View):
    def get(self, request, *args, **kwargs):
        return JsonResponse({'message': 'Welcome to the content moderation API! Please navigate to api to use the services.'})
