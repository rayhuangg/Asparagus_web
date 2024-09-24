from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name=''),
    path('scan/', views.scan),
    path('lidar2dData/', views.Lidar2dData.as_view()),
    path('getLidarDataSample/', views.get_lidar_data_sample, name='getLidarDataSample'),
]