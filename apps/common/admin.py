from django.contrib import admin
from .models import Files

# Register your models here.


class FileModelAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'size', 'url')
    list_filter = ('type', )
    search_fields = ('name', 'type', 'url')
    ordering = ('-created_at',)

    fieldsets = (
        ('File Info', {
            'fields': ('name', 'type', 'size', 'url')
        }),
    )


admin.site.register(Files, FileModelAdmin)
