from django.db import models
from django.conf import settings


class ModerationStatus(models.Model):
    """Справочник статусов модерации"""
    name = models.CharField(max_length=50, unique=True, verbose_name='Название статуса')
    
    class Meta:
        verbose_name = 'Статус модерации'
        verbose_name_plural = 'Статусы модерации'
        ordering = ['id']
    
    def __str__(self):
        return self.name


class ModerationLog(models.Model):
    """Журнал действий модераторов"""
    
    # ИСПРАВЛЕНИЕ: Используем строку вместо импорта класса
    photo = models.ForeignKey(
        'photos.RetroPhoto',
        on_delete=models.CASCADE,
        related_name='moderation_history',
        verbose_name='Фотография'
    )
    moderator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True, blank=True,          # <-- добавить
        related_name='moderation_actions',
        verbose_name='Модератор'
    )   
    review_date = models.DateTimeField(auto_now_add=True, verbose_name='Дата проверки')
    comment = models.TextField(blank=True, verbose_name='Комментарий модератора')
    
    class Meta:
        verbose_name = 'Запись журнала модерации'
        verbose_name_plural = 'Журнал модерации'
        ordering = ['-review_date']
    
    def __str__(self):
        return f"{self.photo} — {self.moderator.username} ({self.review_date.strftime('%d.%m.%Y')})"