from django.http import HttpResponse, Http404, HttpResponseNotFound, HttpResponseForbidden, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from .models import ProductVariant, Product, Favorite, OrderItem, Order, Category, Cart, Profile
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required



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

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    selected_materials = request.GET.getlist('materials')
    selected_inserts = request.GET.getlist('inserts')
    selected_genders = request.GET.getlist('genders')

    if selected_materials:
        products = products.filter(material__in=selected_materials)
    if selected_inserts:
        products = products.filter(insertion__in=selected_inserts)
    if selected_genders:
        products = products.filter(gender__in=selected_genders)

    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    if min_price: products = products.filter(base_price__gte=min_price)
    if max_price: products = products.filter(base_price__lte=max_price)

    sort = request.GET.get('sort')
    if sort == 'price_asc':
        products = products.order_by('base_price')
    elif sort == 'price_desc':
        products = products.order_by('-base_price')

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


def register(request):
    if request.method == 'POST':
        u_name = request.POST.get('username')
        email = request.POST.get('email')
        p_name = request.POST.get('full_name')
        pass1 = request.POST.get('pass1')
        pass2 = request.POST.get('pass2')

        if len(pass1) < 8:
            messages.error(request, "Пароль должен содержать минимум 8 символов")
            return redirect('register')

        if pass1.isdigit():
            messages.error(request, "Пароль не может состоять только из цифр")
            return redirect('register')

        if pass1 != pass2:
            messages.error(request, "Пароли не совпадают")
            return redirect('register')

        if User.objects.filter(username=u_name).exists():
            messages.error(request, "Такой логин уже занят")
            return redirect('register')

        user = User.objects.create_user(username=u_name, email=email, password=pass1)

        # после сигнала
        profile = user.profile
        profile.full_name = p_name
        profile.save()

        login(request, user)
        merge_carts(request, user)  # объединяем корзину сразу
        return redirect('catalog')

    return render(request, 'shop/register.html')


def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # проверка
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            merge_carts(request, user) # склеиваем данные до входа + после входа
            return redirect('home')
        else:
            messages.error(request, "Неверный логин или пароль")

    return render(request, 'shop/login.html')

def user_logout(request):
    logout(request)
    return redirect('home')

@login_required(login_url='login')
def profile_view(request):
    return render(request, 'shop/profile.html')

# корзина и заказы

def merge_carts(request, user):
    # переносит товары из анонимной сессии в аккаунт пользователя
    session_key = request.session.session_key
    if session_key:
        guest_items = Cart.objects.filter(session_key=session_key)
        for item in guest_items:
            user_item = Cart.objects.filter(user=user, product=item.product).first()
            if user_item:
                user_item.quantity += item.quantity
                user_item.save()
                item.delete()
            else:
                item.user = user
                item.session_key = None
                item.save()


def add_to_cart(request, product_id):
    if not request.session.session_key:
        request.session.create()

    session_id = request.session.session_key
    product = get_object_or_404(Product, id=product_id)

    variant_id = request.POST.get('variant_id')
    if not variant_id:
        messages.error(request, "Пожалуйста, выберите размер")
        return redirect(request.META.get('HTTP_REFERER', 'catalog'))

    variant = get_object_or_404(ProductVariant, id=variant_id)

    if variant.stock <= 0:
        messages.error(request, f"Размера {variant.size} нет в наличии")
        return redirect(request.META.get('HTTP_REFERER', 'catalog'))

    user = request.user if request.user.is_authenticated else None

    if user:
        cart_item, created = Cart.objects.get_or_create(
            user=user,
            product=product,
            variant=variant
        )
    else:
        cart_item, created = Cart.objects.get_or_create(
            session_key=session_id,
            product=product,
            variant=variant
        )

    if not created:
        cart_item.quantity += 1
    else:
        cart_item.quantity = 1

    cart_item.save()
    return redirect('cart')


def cart(request):
    if request.user.is_authenticated:
        cart_items = Cart.objects.filter(user=request.user)
    else:
        session_id = request.session.session_key
        cart_items = Cart.objects.filter(session_key=session_id) if session_id else []

    total_price = sum(item.product.base_price * item.quantity for item in cart_items)

    return render(request, 'shop/cart.html', {
        'cart_items': cart_items,
        'total_price': total_price
    })


@login_required(login_url='login')
def checkout(request):
    cart_items = Cart.objects.filter(user=request.user)

    if not cart_items.exists():
        return redirect('catalog')

    user_profile = request.user.profile

    if request.method == 'POST':
        total_price = sum(item.product.base_price * item.quantity for item in cart_items)

        # проверка остатков
        for item in cart_items:
            if not item.variant or item.variant.stock < item.quantity:
                messages.error(request, f"Товар {item.product.title} (размер {item.variant.size}) закончился")
                return redirect('cart')

        order = Order.objects.create(
            user=request.user,
            full_name=request.POST.get('full_name'),
            phone=request.POST.get('phone'),
            address=request.POST.get('address'),
            total_price=total_price
        )

        for item in cart_items:
            variant = item.variant

            variant.stock -= item.quantity
            variant.save()

            OrderItem.objects.create(
                order=order,
                product=item.product,
                price_at_order=item.product.base_price,
                quantity=item.quantity
            )

        cart_items.delete()

    return render(request, 'shop/checkout.html', {
        'cart_items': cart_items,
        'profile': user_profile
    })

def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(Cart, id=item_id)
    if cart_item.user == request.user or cart_item.session_key == request.session.session_key:
        cart_item.delete()
    return redirect('cart')



def favorites(request):
    return render(request, 'shop/favorites.html')

def about(request):
    return render(request, 'shop/about.html')

def contacts(request):
    return render(request, 'shop/contacts.html')