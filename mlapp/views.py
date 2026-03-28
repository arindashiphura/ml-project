import json

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .analytics import get_daily_activity_series, log_event
from .climate_service import (
    REGIONS,
    assess_climate_risks,
    forecast_next_week_rainfall,
)
from .forms import RiskAssessmentForm, WeatherForecastForm
from .ml_service import SPECIES, predict_species
from .models import AnalyticsEvent


def home(request):
    return render(
        request,
        "mlapp/home.html",
        {
            "regions": REGIONS,
        },
    )


def dashboard(request):
    chart_series, week_total, peak_day = get_daily_activity_series(days=7)
    return render(
        request,
        "mlapp/dashboard.html",
        {
            "regions": REGIONS,
            "chart_series": chart_series,
            "analytics_week_total": week_total,
            "analytics_peak_day": peak_day,
        },
    )


def sector_agriculture(request):
    return render(request, "mlapp/sector_agriculture.html", {"regions": REGIONS})


def sector_energy(request):
    return render(request, "mlapp/sector_energy.html", {"regions": REGIONS})


def sector_government(request):
    return render(request, "mlapp/sector_government.html", {"regions": REGIONS})


def tools_weather(request):
    forecast = None
    risk = None
    if request.method == "POST":
        form = WeatherForecastForm(request.POST)
        if form.is_valid():
            forecast = forecast_next_week_rainfall(
                region_id=form.cleaned_data["region"],
                month=form.cleaned_data["month"],
                temp_c=form.cleaned_data["temp_c"],
                humidity_pct=form.cleaned_data["humidity_pct"],
                recent_rain_mm=form.cleaned_data["recent_rain_mm"],
            )
            risk = assess_climate_risks(
                forecast_mm=forecast.next_week_rain_mm,
                month=form.cleaned_data["month"],
                recent_dry_spell_days=0,
                flood_events_30d=0,
            )
            log_event(
                AnalyticsEvent.EventType.FORECAST_WEB,
                region_id=form.cleaned_data["region"],
            )
    else:
        form = WeatherForecastForm()
    return render(
        request,
        "mlapp/tools_weather.html",
        {"form": form, "forecast": forecast, "risk": risk},
    )


def tools_risk(request):
    breakdown = None
    forecast = None
    if request.method == "POST":
        form = RiskAssessmentForm(request.POST)
        if form.is_valid():
            forecast = forecast_next_week_rainfall(
                region_id=form.cleaned_data["region"],
                month=form.cleaned_data["month"],
                temp_c=24.0,
                humidity_pct=68.0,
                recent_rain_mm=form.cleaned_data["recent_rain_mm"],
            )
            breakdown = assess_climate_risks(
                forecast_mm=forecast.next_week_rain_mm,
                month=form.cleaned_data["month"],
                recent_dry_spell_days=form.cleaned_data["recent_dry_spell_days"],
                flood_events_30d=form.cleaned_data["flood_events_30d"],
            )
            log_event(
                AnalyticsEvent.EventType.RISK_WEB,
                region_id=form.cleaned_data["region"],
            )
    else:
        form = RiskAssessmentForm()
    return render(
        request,
        "mlapp/tools_risk.html",
        {"form": form, "breakdown": breakdown, "forecast": forecast},
    )


@csrf_exempt
@require_http_methods(["POST"])
def api_climate_forecast(request):
    try:
        body = json.loads(request.body.decode() or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    try:
        f = forecast_next_week_rainfall(
            region_id=body["region_id"],
            month=int(body["month"]),
            temp_c=float(body["temp_c"]),
            humidity_pct=float(body["humidity_pct"]),
            recent_rain_mm=float(body["recent_rain_mm"]),
        )
    except (KeyError, TypeError, ValueError) as e:
        return JsonResponse({"error": str(e)}, status=400)
    log_event(AnalyticsEvent.EventType.FORECAST_API, region_id=f.region_id)
    return JsonResponse(
        {
            "region_id": f.region_id,
            "month": f.month,
            "next_week_rain_mm": f.next_week_rain_mm,
            "band": f.band,
            "summary": f.summary,
        }
    )


@csrf_exempt
@require_http_methods(["POST"])
def api_climate_risk(request):
    try:
        body = json.loads(request.body.decode() or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    try:
        forecast_mm = float(body["forecast_mm"])
        month = int(body["month"])
        dry_days = int(body.get("recent_dry_spell_days", 0))
        floods = int(body.get("flood_events_30d", 0))
        b = assess_climate_risks(
            forecast_mm=forecast_mm,
            month=month,
            recent_dry_spell_days=dry_days,
            flood_events_30d=floods,
        )
    except (KeyError, TypeError, ValueError) as e:
        return JsonResponse({"error": str(e)}, status=400)
    log_event(AnalyticsEvent.EventType.RISK_API)
    return JsonResponse(
        {
            "level": b.level,
            "score": b.score,
            "agriculture": b.agriculture,
            "energy": b.energy,
            "government": b.government,
            "drivers": b.drivers,
        }
    )


@csrf_exempt
@require_http_methods(["POST"])
def api_predict_iris(request):
    try:
        body = json.loads(request.body.decode() or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    features = body.get("features")
    if not isinstance(features, list):
        return JsonResponse(
            {"error": 'Body must include "features" as a list of numbers'},
            status=400,
        )
    try:
        nums = [float(x) for x in features]
    except (TypeError, ValueError):
        return JsonResponse({"error": "All features must be numbers"}, status=400)
    try:
        idx, name = predict_species(nums)
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400)
    log_event(AnalyticsEvent.EventType.IRIS_API)
    return JsonResponse(
        {
            "species_index": idx,
            "species": name,
            "species_options": SPECIES,
        }
    )
