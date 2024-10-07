from django.urls import path
from .views import CheckoutView, CheckoutFinalizationView, CreatePaymentIntentView, StripeWebhookView

urlpatterns = [
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('checkout/finalize/', CheckoutFinalizationView.as_view(), name='checkout-finalize'),
    path('create-intent/', CreatePaymentIntentView.as_view(), name='create-intent'),
    path('webhook/', StripeWebhookView.as_view(), name='stripe-webhook'),
]
