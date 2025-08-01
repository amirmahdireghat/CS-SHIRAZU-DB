from django.db import models
from django.utils import timezone


class user_data(models.Model):
    id = models.BigIntegerField(primary_key=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=150, blank=True, null=True)
    username = models.CharField(max_length=100, blank=True, null=True)
    number = models.BigIntegerField()
    token = models.IntegerField(blank=True,null=True)
    selected_prompt = models.IntegerField(default=2);
    selected_llm = models.CharField(max_length=30, default="gpt-4o")
    created_at = models.DateTimeField(auto_now_add=True)  # removed `default` and `null`

    def __str__(self):
        return str(self.id)
    
class Chat(models.Model):  # Class names should use CamelCase as per Django conventions
    id = models.AutoField(primary_key=True)  # Auto-incrementing ID field
    user_id = models.ForeignKey(user_data, on_delete=models.CASCADE)  # Set 'on_delete' to prevent errors
    message = models.TextField()  # Fix typo
    response = models.TextField()
    media_url = models.CharField(max_length=500, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Chat {self.id} by User {self.user_id}"

class prompt(models.Model):
    prompt_id = models.IntegerField(primary_key=True)
    prompt_text = models.TextField()
    description = models.CharField(max_length=150, blank=True, null=True)

class bot_text(models.Model):
    key = models.CharField(max_length=50, unique=True, help_text="Unique identifier for the text")
    content = models.TextField(help_text="Content of the text to be displayed by the bot", blank=True)
    description = models.CharField(max_length=100, blank=True, help_text="Description of the text's purpose")

    def __str__(self):
        return self.key
    
class SaleEvent(models.Model):
    name = models.CharField(max_length=50)
    free_tokens = models.IntegerField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    eligible_duration = models.DurationField(
        null=True,
        blank=True,
        help_text="Only users who registered within this duration from now are eligible. For example, use '90 days' for a 3-month eligibility."
    )

    def __str__(self):
        return self.name

class SaleClaim(models.Model):
    user = models.ForeignKey(user_data, on_delete=models.CASCADE)  # or use your custom user model, e.g., user_data
    sale_event = models.ForeignKey(SaleEvent, on_delete=models.CASCADE)
    claimed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'sale_event')

    def __str__(self):
        return f"{self.user} - {self.sale_event}"
