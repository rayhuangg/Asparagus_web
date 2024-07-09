from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name=''),
    # path('UpdataVehicleData/', views.update_vehicle_data),
    # path('GetVehicleData/', views.get_vehicle_data),

    # POST immediately data, GET newest data
    path("vehicleData/", views.VehicleRealTimeData.as_view()),

    # Update experiment info (start, end time, fertilizer and total amount)
    path("expData/", views.update_experiment_info, name="ExpData"),

    # GET all fertilizers, POST a new fertilizer
    path('fertilizers/', views.FertilizerListView.as_view(), name='fertilizer-list'),


]