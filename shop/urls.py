from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),

    path('catalog/', views.catalog, name='catalog'),
    path('catalog/<slug:category_slug>/', views.catalog, name='category_filter'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    path('about/', views.about, name='about'),
    path('contacts/', views.contacts, name='contacts'),
    path('favorite/toggle/<int:product_id>/', views.toggle_favorite, name='toggle_favorite'),
    path('favorites/', views.favorites, name='favorites'),
    path('cart/', views.cart, name='cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('register/', views.register, name='register'),
    path('profile/', views.profile_view, name='profile'),
]