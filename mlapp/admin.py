from django.contrib import admin

from .models import AnalyticsEvent


@admin.register(AnalyticsEvent)
class AnalyticsEventAdmin(admin.ModelAdmin):
    list_display = ("event_type", "region_id", "created_at")
    list_filter = ("event_type",)
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
