from django.urls import path
from . import views

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('v1/moderate/text', views.ModerateText.as_view(), name='moderate'),
]