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
    categories = Category.objects.all()
    products = Product.objects.all()

    query = request.GET.get('q')
    if query:
        products = products.filter(title__iregex=query)

# категория

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

# материал, вставка, пол

    selected_materials = request.GET.getlist('materials')
    selected_inserts = request.GET.getlist('inserts')
    selected_genders = request.GET.getlist('genders')

    if selected_materials:
        products = products.filter(material__in=selected_materials)
    if selected_inserts:
        products = products.filter(insertion__in=selected_inserts)
    if selected_genders:
        products = products.filter(gender__in=selected_genders)

# прайс

    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    if min_price: products = products.filter(base_price__gte=min_price)
    if max_price: products = products.filter(base_price__lte=max_price)

    sort = request.GET.get('sort')
    if sort == 'price_asc': products = products.order_by('base_price')
    elif sort == 'price_desc': products = products.order_by('-base_price')

    return render(request, 'shop/catalog.html', {
        'category': category,
        'categories': categories,
        'products': products,
        'query': query,
        'selected_materials': selected_materials,
        'selected_inserts': selected_inserts,
        'selected_genders': selected_genders,
        'sort': sort,
        'min_price': min_price,
        'max_price': max_price
    })


def cart(request):
    return render(request, 'shop/cart.html')

def favorites(request):
    return render(request, 'shop/favorites.html')

def about(request):
    return render(request, 'shop/about.html')

def contacts(request):
    return render(request, 'shop/contacts.html')
