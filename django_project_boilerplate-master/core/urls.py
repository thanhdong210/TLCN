from django.urls import path, include

from .views import (
    item_list, 
    HomeView, 
    ItemDetailView, 
    add_to_cart, 
    remove_from_cart, 
    OrderSummaryView, 
    remove_single_item_from_cart,
    add_single_item_to_cart,
    remove_the_item_from_cart,
    checkout,
    PaymentOption,
    AddCouponView,
    RefundView
)
from . import views
from django.contrib.auth import views as auth_views

app_name = 'core'

urlpatterns = [
    path('accounts/', include('allauth.urls')),    

    path('', HomeView.as_view(), name='home'),    

    path('checkout/', checkout.as_view(), name='checkout'),

    path('order-summary-view/', OrderSummaryView.as_view(), name='order-summary'),

    path('product/<slug>/', ItemDetailView.as_view(), name='product'),

    path('add-to-cart/<slug>/', add_to_cart, name='add-to-cart'),
    path('add-single-item-to-cart/<slug>/', add_single_item_to_cart, name='add-single-item-to-cart'),
    path('remove-from-cart/<slug>/', remove_from_cart, name='remove-from-cart'),
    path('remove-single-item-from-cart/<slug>/', remove_single_item_from_cart, name='remove-single-item-from-cart'),
    path('remove-the-item-from-cart/<slug>/', remove_the_item_from_cart, name='remove-the-item-from-cart'),

    path('login/', auth_views.LoginView.as_view(template_name="login.html"), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('signup/', views.register, name="register"), 

    path('payment/<payment_option>', PaymentOption.as_view(), name='payment'), 
    path('payment/', PaymentOption.as_view(), name='payment'),

    path('add-coupon/', AddCouponView.as_view(), name='add-coupon'),

    path('request-refund/', RefundView.as_view(), name='request-refund'),

    path('search/', views.search, name='search'),

    path('rau/', views.CategoryRau, name='rau'),
    path('cu/', views.CategoryCu, name='cu'),

]