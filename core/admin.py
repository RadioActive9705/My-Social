from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Profile

# admin.site.register(CustomUser, UserAdmin)
# admin.site.register(Profile)
# # Register your models here.

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display=('user','bio')
    search_fields=('user_username',)


    
