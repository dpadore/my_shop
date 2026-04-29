from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),

    path('catalog/', views.catalog, name='catalog'),
    path('catalog/<slug:category_slug>/', views.catalog, name='category_filter'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    path('about/', views.about, name='about'),
    path('contacts/', views.contacts, name='contacts'),
    path('favorites/', views.favorites, name='favorites'),
    path('cart/', views.cart, name='cart'),
]