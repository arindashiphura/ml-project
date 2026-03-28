from django import forms

from .climate_service import REGIONS


class WeatherForecastForm(forms.Form):
    region = forms.ChoiceField(
        choices=[(r["id"], r["name"]) for r in REGIONS],
        label="Region",
    )
    month = forms.IntegerField(min_value=1, max_value=12, initial=3)
    temp_c = forms.FloatField(
        label="Recent avg temperature (°C)",
        min_value=10,
        max_value=40,
        initial=24.0,
    )
    humidity_pct = forms.FloatField(
        label="Relative humidity (%)",
        min_value=20,
        max_value=100,
        initial=70.0,
    )
    recent_rain_mm = forms.FloatField(
        label="Rainfall last 7 days (mm)",
        min_value=0,
        max_value=500,
        initial=40.0,
    )


class RiskAssessmentForm(forms.Form):
    region = forms.ChoiceField(choices=[(r["id"], r["name"]) for r in REGIONS])
    month = forms.IntegerField(min_value=1, max_value=12, initial=4)
    recent_rain_mm = forms.FloatField(
        label="Rainfall last 7 days (mm)",
        min_value=0,
        max_value=500,
        initial=35.0,
    )
    recent_dry_spell_days = forms.IntegerField(
        label="Consecutive days with negligible rain",
        min_value=0,
        max_value=120,
        initial=5,
    )
    flood_events_30d = forms.IntegerField(
        label="Heavy rain / flood events in last 30 days (count)",
        min_value=0,
        max_value=30,
        initial=0,
    )
