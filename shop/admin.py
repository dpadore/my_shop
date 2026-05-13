from django.contrib import admin
from .models import Category, Product, ProductVariant, Order, OrderItem, Favorite, Cart, Profile

admin.site.register(Category)
admin.site.register(Product)
admin.site.register(ProductVariant)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Favorite)
admin.site.register(Profile)
admin.site.register(Cart)