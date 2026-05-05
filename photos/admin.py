from django.contrib import admin
from .models import RetroPhoto


@admin.register(RetroPhoto)
class RetroPhotoAdmin(admin.ModelAdmin):
    list_display = ['id', 'year', 'azimuth', 'location', 'owner', 'status', 'created_at']
    list_filter = ['status', 'year', 'location__location_type']
    search_fields = ['description', 'location__name']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        (None, {
            'fields': ('image', 'year', 'azimuth', 'description')
        }),
        ('Связи', {
            'fields': ('location', 'owner', 'status')
        }),
        ('Служебное', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('location', 'owner', 'status')