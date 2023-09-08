# api/urls.py
from django.urls import path
from .views import  ResultListView

urlpatterns = [
    path('demoID/<str:demoID>/', ResultListView.as_view(), name='demoID'),
]