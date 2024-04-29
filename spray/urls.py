from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name=''),
    # path('UpdataVehicleData/', views.update_vehicle_data),
    # path('GetVehicleData/', views.get_vehicle_data),
    path("VehicleData/", views.VehicleRealTimeData.as_view()),
    path("ExpData/", views.update_experiment_info, name="ExpData")

]