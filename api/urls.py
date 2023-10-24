# api/urls.py
from django.urls import path
from .views import  ResultListView, BatchSearchView

urlpatterns = [
    path('section/<str:sectionName>/', ResultListView.as_view(), name='sectionName'),
    path('batch/<int:batchId>/', BatchSearchView.as_view(), name='batchId')
]