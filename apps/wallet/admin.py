from django.contrib import admin
from .models import Wallet


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'current_earnings',
        'total_earnings',
        'total_withdraws',
        'is_site_wallet',
        'deleted_at'
    )
    list_filter = ('is_site_wallet', 'deleted_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    
    fieldsets = (
        ('Wallet Information', {
            'fields': (
                'user',
                'current_earnings',
                'total_earnings',
                'total_withdraws',
                'is_site_wallet'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'deleted_at')
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at', 'deleted_at')