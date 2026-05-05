from django.contrib import admin
from .models import ModerationStatus, ModerationLog


@admin.register(ModerationStatus)
class ModerationStatusAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    search_fields = ['name']


@admin.register(ModerationLog)
class ModerationLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'photo', 'moderator', 'review_date']
    list_filter = ['moderator', 'review_date']
    readonly_fields = ['photo', 'moderator', 'review_date', 'comment']
    
    def has_add_permission(self, request):
        return False  # Записи создаются автоматически