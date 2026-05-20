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

    is_in_favorites = False
    if request.user.is_authenticated:
        is_in_favorites = Favorite.objects.filter(user=request.user, product=product).exists()
    else:
        session_id = request.session.session_key
        if session_id:
            is_in_favorites = Favorite.objects.filter(session_key=session_id, product=product).exists()

    return render(request, 'shop/product_detail.html', {
        'product': product,
        'is_in_favorites': is_in_favorites
    })


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

        context = {
            'username': u_name,
            'email': email,
            'full_name': p_name,
        }

        if len(pass1) < 8:
            context['error_message'] = "Пароль должен содержать минимум 8 символов"
            return render(request, 'shop/register.html', context)

        if pass1.isdigit():
            context['error_message'] = "Пароль не может состоять только из цифр"
            return render(request, 'shop/register.html', context)

        if pass1 != pass2:
            context['error_message'] = "Пароли не совпадают"
            return render(request, 'shop/register.html', context)

        if User.objects.filter(username=u_name).exists():
            context['error_message'] = "Такой логин уже занят"
            return render(request, 'shop/register.html', context)

        user = User.objects.create_user(username=u_name, email=email, password=pass1)

        # После сигнала профиль создается автоматически
        profile = user.profile
        profile.full_name = p_name
        profile.save()

        merge_carts(request, user)
        login(request, user)
        return redirect('catalog')

    return render(request, 'shop/register.html')


def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            merge_carts(request, user)
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, "Неверный логин или пароль")

    return render(request, 'shop/login.html')


def user_logout(request):
    logout(request)
    return redirect('home')


@login_required(login_url='login')
def profile_view(request):
    user = request.user
    profile = user.profile

    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')

        if not full_name or not email:
            messages.error(request, "Поля Имя и Email должны быть заполнены")
            return redirect('profile')

        user.email = email
        user.save()

        profile.full_name = full_name
        profile.phone = phone
        profile.address = address
        profile.save()

        messages.success(request, "Профиль успешно обновлен!")
        return redirect('profile')

    orders = Order.objects.filter(user=user).order_by('-id')

    return render(request, 'shop/profile.html', {
        'user': user,
        'profile': profile,
        'orders': orders
    })


def merge_carts(request, user):
    session_key = request.session.session_key

    if not session_key:
        print("Предупреждение: session_key не найден в текущем запросе!")
        return

    guest_items = Cart.objects.filter(session_key=session_key)

    for item in guest_items:
        user_item = Cart.objects.filter(user=user, product=item.product, variant=item.variant).first()
        if user_item:
            user_item.quantity += item.quantity
            user_item.save()
            item.delete()
        else:
            item.user = user
            item.session_key = None
            item.save()

    guest_favorites = Favorite.objects.filter(session_key=session_key)

    for fav in guest_favorites:
        user_fav_exists = Favorite.objects.filter(user=user, product=fav.product).exists()
        if user_fav_exists:
            fav.delete()
        else:
            fav.user = user
            fav.session_key = None
            fav.save()



def add_to_cart(request, product_id):
    if not request.session.session_key:
        request.session.create()

    session_id = request.session.session_key
    request.session.modified = True

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

        return render(request, 'shop/catalog.html')

    return render(request, 'shop/checkout.html', {
        'cart_items': cart_items,
        'profile': user_profile
    })


def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(Cart, id=item_id)
    if cart_item.user == request.user or cart_item.session_key == request.session.session_key:
        cart_item.delete()
    return redirect('cart')


def toggle_favorite(request, product_id):
    if not request.session.session_key:
        request.session.create()

    session_id = request.session.session_key
    request.session.modified = True

    product = get_object_or_404(Product, id=product_id)
    user = request.user if request.user.is_authenticated else None

    if user:
        favorite_item = Favorite.objects.filter(user=user, product=product)
    else:
        favorite_item = Favorite.objects.filter(session_key=session_id, product=product)

    if favorite_item.exists():
        favorite_item.delete()
        messages.error(request, f"Товар {product.title} удален из избранного")
    else:
        if user:
            Favorite.objects.create(user=user, product=product)
        else:
            Favorite.objects.create(session_key=session_id, product=product)
        messages.success(request, f"Товар {product.title} добавлен в избранное")

    return redirect(request.META.get('HTTP_REFERER', 'catalog'))


def favorites(request):
    if request.user.is_authenticated:
        favorite_items = Favorite.objects.filter(user=request.user)
    else:
        session_id = request.session.session_key
        favorite_items = Favorite.objects.filter(session_key=session_id) if session_id else []

    products = [item.product for item in favorite_items]
    return render(request, 'shop/favorites.html', {'products': products})


def about(request):
    return render(request, 'shop/about.html')


def contacts(request):
    return render(request, 'shop/contacts.html')