from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("sectors/agriculture/", views.sector_agriculture, name="sector_agriculture"),
    path("sectors/energy/", views.sector_energy, name="sector_energy"),
    path(
        "sectors/government/",
        views.sector_government,
        name="sector_government",
    ),
    path("tools/weather/", views.tools_weather, name="tools_weather"),
    path("tools/risk/", views.tools_risk, name="tools_risk"),
    path("api/climate/forecast/", views.api_climate_forecast, name="api_climate_forecast"),
    path("api/climate/risk/", views.api_climate_risk, name="api_climate_risk"),
    path("api/lab/iris/", views.api_predict_iris, name="api_predict_iris"),
]
