from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name=''),
    path('scan/', views.scan)
]