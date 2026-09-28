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


class Shop(models.Model):
    """Магазин (поставщик)."""
    name = models.CharField('Название', max_length=50)
    # ссылка на файл с прайсом, откуда грузим товары
    url = models.URLField('Ссылка на прайс', null=True, blank=True)
    # у каждого магазина есть свой пользователь с типом shop
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True,
                                related_name='shop', verbose_name='Пользователь')
    # магазин может временно не принимать заказы
    state = models.BooleanField('Принимает заказы', default=True)

    class Meta:
        verbose_name = 'Магазин'
        verbose_name_plural = 'Магазины'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Category(models.Model):
    """Категория товаров. Одна категория может быть у нескольких магазинов."""
    name = models.CharField('Название', max_length=50)
    shops = models.ManyToManyField(Shop, related_name='categories', blank=True,
                                   verbose_name='Магазины')

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Product(models.Model):
    """Товар в общем каталоге (без цены, цены у каждого магазина свои)."""
    name = models.CharField('Название', max_length=100)
    category = models.ForeignKey(Category, on_delete=models.CASCADE,
                                 related_name='products', verbose_name='Категория')

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'
        ordering = ('name',)

    def __str__(self):
        return self.name


class ProductInfo(models.Model):
    """Товар в конкретном магазине: цена, остаток и т.д."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE,
                                related_name='product_infos', verbose_name='Товар')
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE,
                             related_name='product_infos', verbose_name='Магазин')
    # id товара из файла магазина
    external_id = models.PositiveIntegerField('Внешний id')
    model = models.CharField('Модель', max_length=100, blank=True)
    quantity = models.PositiveIntegerField('Количество')
    price = models.PositiveIntegerField('Цена')
    price_rrc = models.PositiveIntegerField('Рекомендуемая цена')

    class Meta:
        verbose_name = 'Информация о товаре'
        verbose_name_plural = 'Информация о товарах'
        # в одном магазине не может быть двух товаров с одним внешним id
        constraints = [
            models.UniqueConstraint(fields=['shop', 'external_id'], name='unique_shop_product'),
        ]

    def __str__(self):
        return f'{self.product} ({self.shop})'


class Parameter(models.Model):
    """Название характеристики, например "Цвет" или "Диагональ"."""
    name = models.CharField('Название', max_length=50)

    class Meta:
        verbose_name = 'Характеристика'
        verbose_name_plural = 'Характеристики'
        ordering = ('name',)

    def __str__(self):
        return self.name


class ProductParameter(models.Model):
    """Значение характеристики у конкретного товара в магазине."""
    product_info = models.ForeignKey(ProductInfo, on_delete=models.CASCADE,
                                     related_name='product_parameters', verbose_name='Товар в магазине')
    parameter = models.ForeignKey(Parameter, on_delete=models.CASCADE,
                                  related_name='product_parameters', verbose_name='Характеристика')
    value = models.CharField('Значение', max_length=100)

    class Meta:
        verbose_name = 'Характеристика товара'
        verbose_name_plural = 'Характеристики товаров'
        constraints = [
            models.UniqueConstraint(fields=['product_info', 'parameter'], name='unique_product_parameter'),
        ]

    def __str__(self):
        return f'{self.parameter}: {self.value}'
