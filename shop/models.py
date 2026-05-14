from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название категории")
    slug = models.SlugField(max_length=100, unique=True, null=True, blank=True)

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    def __str__(self):
        return self.name


class Product(models.Model):
    MATERIAL_CHOICES = [
        ('gold', 'Золото'),
        ('rose gold', 'Розовое золото'),
        ('white gold', 'Белое золото'),
        ('silver', 'Серебро'),
        ('platinum', 'Платина'),
    ]
    INSERT_CHOICES = [
        ('diamond', 'Бриллиант'),
        ('emerald', 'Изумруд'),
        ('pearl', 'Жемчуг'),
        ('none', 'Без вставки'),
    ]
    GENDER_CHOICES = [
        ('women', 'Женщинам'),
        ('men', 'Мужчинам'),
        ('unisex', 'Унисекс'),
    ]

    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products', verbose_name="Категория")
    title = models.CharField(max_length=255, verbose_name="Название изделия")
    description = models.TextField(verbose_name="Описание")
    base_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Базовая цена")

    material = models.CharField(max_length=30, choices=MATERIAL_CHOICES, blank=True, null=True, verbose_name="Материал")
    insertion = models.CharField(max_length=30, choices=INSERT_CHOICES, blank=True, null=True, verbose_name="Вставка")
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='women', verbose_name="Для кого")

    sample = models.IntegerField(verbose_name="Проба")
    image = models.ImageField(upload_to='products/', null=True, blank=True, verbose_name="Изображение")

    class Meta:
        verbose_name = "Изделие"
        verbose_name_plural = "Изделия"

    def __str__(self):
        return self.title


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants', verbose_name="Изделие")
    size = models.DecimalField(max_digits=4, decimal_places=1, verbose_name="Размер", null=True)
    stock = models.PositiveIntegerField(default=0, verbose_name="Количество на складе")

    class Meta:
        verbose_name = "Вариант изделия"
        verbose_name_plural = "Варианты изделий (размеры)"

    def __str__(self):
        return f"{self.product.title} - Размер: {self.size}"


# пользователь и профиль

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name="Профиль")
    phone = models.CharField(max_length=20, unique=True, null=True, blank=True, verbose_name="Номер телефона")
    full_name = models.CharField(max_length=255, blank=True, verbose_name="ФИО")
    address = models.TextField(blank=True, verbose_name="Адрес доставки по умолчанию")

    class Meta:
        verbose_name = "Профиль"
        verbose_name_plural = "Профили"

    def __str__(self):
        return f"Профиль: {self.user.username}"

# сигнал
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

# корзина

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name="carts", verbose_name="Корзина")
    session_key = models.CharField(max_length=40, null=True, blank=True, verbose_name="Ключ сессии")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Товар")
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True,verbose_name="Размер/Вариант")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Количество")
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Корзина"
        verbose_name_plural = "Корзины"

    def __str__(self):
        size_info = f" (Размер: {self.variant.size})" if self.variant else ""
        return f"{self.product.title}{size_info} — {self.quantity} шт."


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='favorites', verbose_name="Избранное")
    session_key = models.CharField(max_length=40, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product', 'session_key')
        verbose_name = "Избранное"
        verbose_name_plural = "Избранное"


# заказы

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидает обработки'),
        ('paid', 'Оплачен'),
        ('shipped', 'Отправлен'),
        ('delivered', 'Доставлен'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Аккаунт")

    # на случай если профиля нет или данные другие
    full_name = models.CharField(max_length=255, verbose_name="ФИО получателя")
    phone = models.CharField(max_length=20, verbose_name="Контактный телефон")
    address = models.TextField(verbose_name="Адрес доставки")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Статус")
    total_price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Итоговая сумма")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата оформления")

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Товар")
    price_at_order = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена при покупке")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Количество")

    class Meta:
        verbose_name = "Товар в заказе"
        verbose_name_plural = "Товары в заказе"