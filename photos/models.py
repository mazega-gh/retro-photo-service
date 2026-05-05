from django.db import models
from django.conf import settings
from locations.models import Location


class RetroPhoto(models.Model):
    """Архивные фотографии с метаданными"""
    image = models.ImageField(
        upload_to='retro_photos/%Y/%m/',
        verbose_name='Изображение',
        help_text='Загрузите архивный снимок'
    )
    year = models.IntegerField(verbose_name='Год съёмки', help_text='Пример: 1950')
    azimuth = models.FloatField(
        null=True, blank=True,
        verbose_name='Азимут съёмки (градусы)',
        help_text='Направление камеры в градусах (0–360)'
    )
    description = models.TextField(blank=True, verbose_name='Описание')
    
    # Связи
    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        related_name='photos',
        verbose_name='Локация'
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='uploaded_photos',
        verbose_name='Загрузивший пользователь'
    )
    
    # ИСПРАВЛЕНИЕ: Используем строку вместо импорта класса
    status = models.ForeignKey(
        'moderation.ModerationStatus', 
        on_delete=models.PROTECT,
        default=1,  # По умолчанию "На проверке"
        related_name='photos',
        verbose_name='Статус модерации'
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата загрузки')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    
    class Meta:
        verbose_name = 'Архивное фото'
        verbose_name_plural = 'Архивные фотографии'
        ordering = ['-year', '-created_at']
        indexes = [
            models.Index(fields=['year']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"Фото {self.year} г. — {self.location.name}"
    
    @property
    def is_published(self):
        """Проверка: опубликовано ли фото"""
        # Обращаемся к имени статуса через точку, так как это объект
        return self.status and self.status.name.lower() == 'опубликовано'