from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    stripe_payment_intent_id = models.CharField(max_length=255, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default='usd')
    status = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    item = models.CharField(max_length=255)

    def __str__(self):
        return f"Transaction of {self.amount} for {self.item} by {self.user.email}"

class Subscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    stripe_subscription_id = models.CharField(max_length=255, unique=True)
    status = models.CharField(max_length=50)
    current_period_end = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
