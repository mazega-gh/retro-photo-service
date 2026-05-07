from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings


class Role(models.Model):
    """Справочник ролей пользователей"""
    name = models.CharField(max_length=50, unique=True, verbose_name='Название роли')
    
    class Meta:
        verbose_name = 'Роль'
        verbose_name_plural = 'Роли'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class User(AbstractUser):
    """Кастомная модель пользователя"""
    email = models.EmailField(null=True, blank=True, verbose_name='Email')
    role = models.ForeignKey(
        Role, 
        on_delete=models.PROTECT, 
        null=True, 
        blank=True,
        related_name='users',
        verbose_name='Роль'
    )
    
    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['username']
    
    def __str__(self):
        return self.username

    def save(self, *args, **kwargs):
        # Автоматически даём права суперпользователя, если роль admin
        if self.role and self.role.name.lower() == 'admin':
            self.is_superuser = True
            self.is_staff = True
        else:
            # Если роль не admin — убираем суперправа (на случай смены роли)
            self.is_superuser = False
            self.is_staff = False
        super().save(*args, **kwargs)
    
    @property
    def is_admin(self):
        # Считаем администратором, если есть роль admin ИЛИ это суперпользователь/сотрудник
        if self.is_superuser or self.is_staff:
            return True
        return self.role is not None and self.role.name.lower() == 'admin'

    @property
    def is_moderator(self):
        # Модератор — либо роль moderator, либо также админ (который наследует права модератора)
        if self.is_admin:
            return True
        return self.role is not None and self.role.name.lower() == 'moderator'