from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name=''),
    path('side/', views.side),
    path('front/', views.front),
    path('refreshFront', views.refreshFront),
    path('demoProgress', views.demoProgress),
    path('showdemoRange', views.showdemoRange),
    path('preview', views.preview),
]