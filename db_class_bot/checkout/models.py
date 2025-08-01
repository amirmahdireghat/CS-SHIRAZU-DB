from django.db import models
from admin_panel.models import user_data

class invoices(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey(user_data, on_delete=models.CASCADE)
    # New field linking to the purchased token package:
    token_plan = models.ForeignKey('token_price', on_delete=models.CASCADE, null=True, blank=True)
    amount = models.BigIntegerField()
    status = models.CharField(max_length=6)
    expires_at = models.DateTimeField(null=True, blank=True)  # If you want to use token expiry

    def __str__(self):
        user = self.user_id
        name = user.first_name if user.first_name else "No Name"
        number = user.number if user.number else "No Number"
        return f"Invoice {self.id} - {name} ({number})"


class token_price(models.Model):
    option = models.AutoField(primary_key=True)
    token = models.IntegerField()
    price = models.BigIntegerField()
    validity_period = models.IntegerField(
        help_text="Validity period in days for these tokens",
        default=30  # Default validity period; adjust as needed.
    )

    def __str__(self):
        return f"Option {self.option}: {self.token} tokens for {self.price} ریال (Valid for {self.validity_period} days)"


class UserTokenPlan(models.Model):
    user = models.ForeignKey(user_data, on_delete=models.CASCADE)
    token_plan = models.ForeignKey(token_price, on_delete=models.CASCADE, null=True, blank=True)
    tokens_remaining = models.IntegerField()
    purchased_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    invoice = models.ForeignKey(invoices, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"UserTokenPlan for {self.user.id}: {self.tokens_remaining} tokens, expires at {self.expires_at}"
