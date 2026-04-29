# Базовый ответ
from django.http import HttpResponse
# Удобные сокращения (самое популярное)
from django.shortcuts import render, get_object_or_404, redirect
# Если нужно генерировать ошибки
from django.http import Http404, HttpResponseNotFound, HttpResponseForbidden
# Для работы с моделями (уже знакомо)
from .models import ProductVariant, Product, Favorite, OrderItem, Order, Category
# Для генерации URL по имени
from django.urls import reverse
# Для JSON-ответов (API)
from django.http import JsonResponse


def home(request):
    products = Product.objects.all()
    return render(request, 'shop/index.html', {'products': products})

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'shop/product_detail.html', {'product': product})


def catalog(request, category_slug=None):
    category = None
    categories = Category.objects.all()  # Получаем все категории для бокового меню
    products = Product.objects.all()

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)  # Фильтруем QuerySet

    return render(request, 'shop/catalog.html', {
        'category': category,
        'categories': categories,
        'products': products
    })

def cart(request):
    return render(request, 'shop/cart.html')

def favorites(request):
    return render(request, 'shop/favorites.html')

def about(request):
    return render(request, 'shop/about.html')

def contacts(request):
    return render(request, 'shop/contacts.html')
