from django.contrib import admin
from import_export import resources
from import_export.admin import ExportMixin
from .models import user_data, Chat, prompt, bot_text, SaleClaim, SaleEvent

# Define resources for each model for import/export operations
class UserDataResource(resources.ModelResource):
    class Meta:
        model = user_data

class ChatResource(resources.ModelResource):
    class Meta:
        model = Chat

class PromptResource(resources.ModelResource):
    class Meta:
        model = prompt

class BotTextResource(resources.ModelResource):
    class Meta:
        model = bot_text

class SaleClaimResource(resources.ModelResource):
    class Meta:
        model = SaleClaim

class SaleEventResource(resources.ModelResource):
    class Meta:
        model = SaleEvent

# Register the user_data model with export functionality
@admin.register(user_data)
class UserDataAdmin(ExportMixin, admin.ModelAdmin):
    list_display = (
        'id', 'first_name', 'last_name', 'username',
        'number', 'token', 'selected_prompt', 'selected_llm', 'created_at'
    )
    search_fields = (
        'id', 'first_name', 'last_name', 'username',
        'number', 'token', 'selected_prompt', 'selected_llm'
    )
    resource_class = UserDataResource

# Register the Chat model with export functionality
@admin.register(Chat)
class ChatAdmin(ExportMixin, admin.ModelAdmin):
    list_display = (
        'id', 'user_id', 'message', 'response', 'media_url', 'timestamp'
    )
    # Search by related user's username, first_name, or last_name along with message content
    search_fields = (
        'user_id__username', 'user_id__first_name', 'user_id__last_name',
        'message', 'response', 'media_url'
    )
    resource_class = ChatResource

# Register the prompt model with export functionality
@admin.register(prompt)
class PromptAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ('prompt_id', 'prompt_text', 'description')
    search_fields = ('prompt_id', 'prompt_text', 'description')
    resource_class = PromptResource

# Register the bot_text model with export functionality
@admin.register(bot_text)
class BotTextAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ('key', 'content', 'description')
    search_fields = ('key', 'content', 'description')
    resource_class = BotTextResource

# Register the SaleClaim model with export functionality
@admin.register(SaleClaim)
class SaleClaimAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ('user', 'sale_event', 'claimed_at')
    search_fields = ('user__username', 'sale_event__name')
    list_filter = ('sale_event', 'claimed_at')
    readonly_fields = ('user', 'sale_event', 'claimed_at')
    resource_class = SaleClaimResource

# Register the SaleEvent model with export functionality
@admin.register(SaleEvent)
class SaleEventAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ('name', 'free_tokens', 'start_time', 'end_time', 'eligible_duration')
    search_fields = ('name', 'free_tokens')
    list_filter = ('start_time', 'end_time')
    resource_class = SaleEventResource
