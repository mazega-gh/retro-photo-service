from django.contrib.gis.db import models as gis_models
from django.db import models


class LocationType(models.Model):
    """Справочник типов локаций"""
    name = models.CharField(max_length=255, unique=True, verbose_name='Название объекта')
    icon_marker = models.CharField(max_length=255, blank=True, verbose_name='Путь к иконке')
    
    class Meta:
        verbose_name = 'Тип локации'
        verbose_name_plural = 'Типы локаций'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Location(models.Model):
    """Географические локации с пространственными координатами"""
    name = models.CharField(max_length=255, verbose_name='Название объекта')
    coordinates = gis_models.PointField(
        srid=4326,  # WGS 84
        verbose_name='Координаты (WGS84)',
        help_text='Точка съёмки в формате широта/долгота'
    )
    location_type = models.ForeignKey(
        LocationType,
        on_delete=models.PROTECT,
        related_name='locations',
        verbose_name='Тип локации',
        null=True,
        blank=True
    )
    created_at = gis_models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    is_approved = models.BooleanField(default=False, verbose_name='Одобрена')
    
    class Meta:
        verbose_name = 'Локация'
        verbose_name_plural = 'Локации'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.coordinates.y:.4f}, {self.coordinates.x:.4f})"
    
    @property
    def latitude(self):
        """Возвращает широту"""
        return self.coordinates.y if self.coordinates else None
    
    @property
    def longitude(self):
        """Возвращает долготу"""
        return self.coordinates.x if self.coordinates else None