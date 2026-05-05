from django.contrib import admin
from django import forms
from django.contrib.gis.forms.widgets import OSMWidget
from django.contrib.gis.db import models as gis_models
from .models import LocationType, Location


class LocationAdminForm(forms.ModelForm):
    """Форма с ручным вводом координат + интерактивная карта"""
    latitude = forms.DecimalField(
        max_digits=9, 
        decimal_places=6,
        help_text='Широта в градусах (например: 57.6299 для Ярославля)',
        initial=57.6299,  # Значение по умолчанию для НОВОЙ локации
        label='Широта (°)',
        required=False
    )
    longitude = forms.DecimalField(
        max_digits=9, 
        decimal_places=6,
        help_text='Долгота в градусах (например: 39.8737 для Ярославля)',
        initial=39.8737,  # Значение по умолчанию для НОВОЙ локации
        label='Долгота (°)',
        required=False
    )
    
    class Meta:
        model = Location
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        """
        Инициализация формы.
        ВАЖНО: Если мы редактируем существующую точку, нужно подставить её координаты в поля,
        иначе там останутся значения по умолчанию (Ярославль).
        """
        super().__init__(*args, **kwargs)
        
        # Если объект уже создан (есть id) и у него есть координаты
        if self.instance and self.instance.pk and self.instance.coordinates:
            self.fields['latitude'].initial = self.instance.coordinates.y
            self.fields['longitude'].initial = self.instance.coordinates.x
    
    def save(self, commit=True):
        """Преобразуем градусы в PointField с правильной проекцией"""
        instance = super().save(commit=False)
        
        from django.contrib.gis.geos import Point
        
        # Если координаты введены вручную в текстовые поля — используем их
        # (Текстовые поля имеют приоритет, если в них что-то вписано)
        if self.cleaned_data.get('latitude') and self.cleaned_data.get('longitude'):
            instance.coordinates = Point(
                float(self.cleaned_data['longitude']),  # X = долгота
                float(self.cleaned_data['latitude']),   # Y = широта
                srid=4326  # WGS 84
            )
        
        if commit:
            instance.save()
        return instance


@admin.register(LocationType)
class LocationTypeAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'icon_marker']
    search_fields = ['name']
    ordering = ['name']


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    # 1. Колонки в общем списке (здесь координаты видны сразу)
    list_display = ['id', 'name', 'location_type', 'get_latitude', 'get_longitude', 'created_at']
    list_filter = ['location_type']
    search_fields = ['name']
    
    # 2. Поля, которые нельзя редактировать (вывод координат)
    readonly_fields = ['created_at', 'get_latitude', 'get_longitude']

    # 3. Настройка интерактивной карты
    formfield_overrides = {
        gis_models.PointField: {'widget': OSMWidget(attrs={
            'default_lat': 57.6299,      # Центр Ярославля
            'default_lon': 39.8737,
            'default_zoom': 13,           # Уровень города
            'map_width': 800,
            'map_height': 500,
            'map_srid': 4326,             # Строго WGS 84
        })},
    }

    def get_fields(self, request, obj=None):
        """
        ЛОГИКА ОТОБРАЖЕНИЯ ПОЛЕЙ:
        
        1. Если мы СОЗДАЕМ новую точку (obj is None):
           Скрываем текстовые поля координат. Оставляем только карту.
           Это решает проблему "пустых полей", так как без JS-файла 
           они всё равно не будут обновляться при клике.
           
        2. Если мы РЕДАКТИРУЕМ точку (obj не None):
           Показываем карту + текстовые поля с текущими координатами (для просмотра).
        """
        if obj is None:
            return ('name', 'location_type', 'coordinates')
        else:
            return ('name', 'location_type', 'coordinates', 'get_latitude', 'get_longitude')

    # Методы для отображения координат в админке
    def get_latitude(self, obj):
        return f"{obj.coordinates.y:.6f}" if obj.coordinates else '-'
    get_latitude.short_description = 'Широта (просмотр)'

    def get_longitude(self, obj):
        return f"{obj.coordinates.x:.6f}" if obj.coordinates else '-'
    get_longitude.short_description = 'Долгота (просмотр)'