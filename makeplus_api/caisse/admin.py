from django.contrib import admin

from .models import BadgePrint


@admin.register(BadgePrint)
class BadgePrintAdmin(admin.ModelAdmin):
    list_display = ('participant', 'event', 'caisse', 'printed_at')
    list_filter = ('event', 'caisse')
    search_fields = ('participant__user__email', 'participant__user__last_name', 'participant__badge_id')
    date_hierarchy = 'printed_at'
    raw_id_fields = ('participant',)
