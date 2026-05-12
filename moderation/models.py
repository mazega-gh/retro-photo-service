from django.conf import settings
from django.db import models


class ModerationStatus(models.Model):
    """Directory of moderation statuses."""

    name = models.CharField(max_length=50, unique=True, verbose_name='Status name')

    class Meta:
        verbose_name = 'Moderation status'
        verbose_name_plural = 'Moderation statuses'
        ordering = ['id']

    def __str__(self):
        return self.name


class ModerationLog(models.Model):
    """Audit trail for moderation actions."""

    photo = models.ForeignKey(
        'photos.RetroPhoto',
        on_delete=models.CASCADE,
        related_name='moderation_history',
        verbose_name='Photo',
    )
    moderator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='moderation_actions',
        verbose_name='Moderator',
    )
    review_date = models.DateTimeField(auto_now_add=True, verbose_name='Review date')
    action = models.CharField(max_length=32, blank=True, verbose_name='Action')
    comment = models.TextField(blank=True, verbose_name='Moderator comment')

    class Meta:
        verbose_name = 'Moderation log entry'
        verbose_name_plural = 'Moderation log'
        ordering = ['-review_date']

    def __str__(self):
        moderator = self.moderator.username if self.moderator else 'System'
        return f'{self.photo} - {moderator} ({self.review_date:%d.%m.%Y})'
