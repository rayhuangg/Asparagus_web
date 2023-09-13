# api/urls.py
from django.urls import path
from .views import  ResultListView

urlpatterns = [
    path('section/<str:sectionName>/', ResultListView.as_view(), name='sectionName'),
]