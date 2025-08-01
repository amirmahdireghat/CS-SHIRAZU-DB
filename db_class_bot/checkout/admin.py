from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import invoices, token_price, UserTokenPlan

class InvoicesAdmin(ImportExportModelAdmin):
    list_display = ('id', 'user_id', 'token_plan', 'amount', 'status', 'expires_at')
    list_filter = ('status',)
    search_fields = ('id', 'user_id__first_name', 'user_id__username')

class TokenPriceAdmin(ImportExportModelAdmin):
    list_display = ('option', 'token', 'price', 'validity_period')
    list_filter = ('validity_period',)
    search_fields = ('option',)

class UserTokenPlanAdmin(ImportExportModelAdmin):
    list_display = ('id', 'user', 'token_plan', 'tokens_remaining', 'purchased_at', 'expires_at', 'invoice')
    list_filter = ('expires_at',)
    search_fields = ('user__first_name', 'user__username', 'token_plan__option')

admin.site.register(invoices, InvoicesAdmin)
admin.site.register(token_price, TokenPriceAdmin)
admin.site.register(UserTokenPlan, UserTokenPlanAdmin)
