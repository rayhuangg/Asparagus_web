from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name=''),
    path('sendDemoId', views.checkDemoId),
    path('sendRange', views.checkRange),
    path('demo/', views.demo),
    path('downloadjson/<int:id>/', views.downloadJSON),
    path('downloadexcel/<int:total_id>/',views.downloadexcel),
    path('updated/', views.updated)
]
