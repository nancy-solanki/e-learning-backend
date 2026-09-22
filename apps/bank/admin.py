from django.contrib import admin
from .models import Bank
# Register your models here.

# admin.site.register(Bank)


class BankModelAdmin(admin.ModelAdmin):

    # The fields to be used in displaying the Bank model.
    # These override the definitions on the ModelAdmin
    list_display = ('name', 'ifsc_code', 'account_number', 'default', 'user', 'deleted_at')
    fieldsets = (
        ('Bank', {
         'fields': ('name', 'ifsc_code', 'account_number', 'default', 'user', 'deleted_at')}),
    )
    add_fieldsets = (
        ("Create Bank", {
            'classes': ('wide',),
            'fields': ('name', 'ifsc_code', 'account_number', 'default', 'user', 'deleted_at'),
        }),
    )
    list_filter = ('default', 'deleted_at')
    search_fields = ('name', 'ifsc_code', 'account_number', 'user')
    ordering = ('default', )
    filter_horizontal = ()


# Now register the new BankModelAdmin...
admin.site.register(Bank, BankModelAdmin)
