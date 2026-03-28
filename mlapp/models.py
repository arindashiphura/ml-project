from django.db import models


class AnalyticsEvent(models.Model):
    """Append-only log for dashboard analytics (forecasts, risk runs, APIs)."""

    class EventType(models.TextChoices):
        FORECAST_WEB = "forecast_web", "Forecast (web form)"
        RISK_WEB = "risk_web", "Risk (web form)"
        FORECAST_API = "forecast_api", "Forecast (API)"
        RISK_API = "risk_api", "Risk (API)"
        IRIS_API = "iris_api", "Iris lab (API)"

    event_type = models.CharField(max_length=32, choices=EventType.choices, db_index=True)
    region_id = models.CharField(max_length=32, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.event_type} @ {self.created_at:%Y-%m-%d %H:%M}"
