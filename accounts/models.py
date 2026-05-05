from django.db import models
from django.contrib.auth.models import AbstractUser


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
    email = models.EmailField(unique=True, verbose_name='Email')
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
    
    @property
    def is_moderator(self):
        return self.role and self.role.name.lower() == 'moderator'
    
    @property
    def is_admin(self):
        return self.role and self.role.name.lower() == 'admin'