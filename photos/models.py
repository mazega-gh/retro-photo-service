from django.conf import settings
from django.db import models
from django.contrib.gis.db import models as gis_models

from locations.models import Location


class RetroPhoto(models.Model):
    """Archived photo with geospatial and historical metadata."""

    image = models.ImageField(
        upload_to='retro_photos/%Y/%m/',
        verbose_name='Image',
        help_text='Upload an archive photo.',
    )
    year = models.IntegerField(verbose_name='Shooting year', help_text='Example: 1950')
    azimuth = models.FloatField(
        null=True,
        blank=True,
        verbose_name='Shooting azimuth',
        help_text='Camera direction in degrees from 0 to 360.',
    )
    description = models.TextField(blank=True, verbose_name='Description')
    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        related_name='photos',
        verbose_name='Location',
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='uploaded_photos',
        verbose_name='Uploader',
    )
    status = models.ForeignKey(
        'moderation.ModerationStatus',
        on_delete=models.PROTECT,
        default=1,
        related_name='photos',
        verbose_name='Moderation status',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created at')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Updated at')
    shooting_point = gis_models.PointField(
        srid=4326,
        null=True,
        blank=True,
        verbose_name='Точка съёмки (где стоял фотограф)',
        help_text='Географическая точка, откуда сделана фотография'
    )
    shooting_azimuth = models.FloatField(
        null=True,
        blank=True,
        verbose_name='Азимут съёмки',
        help_text='Направление камеры от точки съёмки в градусах (0-360)'
    )

    class Meta:
        verbose_name = 'Archive photo'
        verbose_name_plural = 'Archive photos'
        ordering = ['-year', '-created_at']
        indexes = [
            models.Index(fields=['year']),
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self):
        return f'Photo {self.year} - {self.location.name}'

    @property
    def is_published(self):
        return self.status and self.status.name == 'Опубликовано'
