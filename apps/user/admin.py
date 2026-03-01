from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

# Register your models here.

class UserModelAdmin(BaseUserAdmin):
    list_display = ('email', 'username', 'first_name', 'last_name', 'profile_picture', 'status')
    list_filter = ('status', )
    fieldsets = (
        ('User Credentials', {'fields': ('email', 'password')}),
        ('Personal info', {
         'fields': ('first_name', 'last_name', 'username', 'profile_picture')}),
        ('Permissions', {'fields': ('status', )}),
    )
    add_fieldsets = (
        ("Register User", {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'username', 'password1', 'password2', 'status'),
        }),
    )
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('status', )
    filter_horizontal = ()

admin.site.register(User, UserModelAdmin)
