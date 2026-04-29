from django.contrib import admin
from .models import Category, Product, ProductVariant, Order, OrderItem, Favorite

# Регистрация моделей для отображения в админке
admin.site.register(Category)
admin.site.register(Product)
admin.site.register(ProductVariant)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Favorite)