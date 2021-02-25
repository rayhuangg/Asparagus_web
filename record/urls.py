from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name=''),
    path('side/', views.side),
    path('front/', views.front),
    # path('demo/', views.demo),

]