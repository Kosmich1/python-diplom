from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models


USER_TYPE_CHOICES = (
    ('shop', 'Магазин'),
    ('buyer', 'Покупатель'),
)


class UserManager(BaseUserManager):
    """Менеджер пользователей: создаём их по email, а не по username."""
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('Нужно указать email')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        # админ сразу активен, ему не надо подтверждать почту
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Пользователь сервиса: покупатель или магазин (поставщик)."""
    # username не нужен, входим по email
    username = None
    email = models.EmailField('Email', unique=True)
    company = models.CharField('Компания', max_length=50, blank=True)
    position = models.CharField('Должность', max_length=50, blank=True)
    type = models.CharField('Тип пользователя', max_length=5,
                            choices=USER_TYPE_CHOICES, default='buyer')
    # пока почта не подтверждена, пользователь неактивен
    is_active = models.BooleanField('Активен', default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('email',)

    def __str__(self):
        return self.email
