from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Profile, Post, FriendRequest, Friendship, Message, Group, GroupMembership, GroupMessage
from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.auth import login as auth_login
from django.contrib.auth import get_user_model

User = get_user_model()


# Register CustomUser if you use it as the AUTH_USER_MODEL
# admin.site.register(CustomUser, UserAdmin)

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'bio')
    search_fields = ('user__username', 'user__email')


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('author', 'created_at')
    search_fields = ('author__username', 'content')


@admin.register(FriendRequest)
class FriendRequestAdmin(admin.ModelAdmin):
    list_display = ('from_user', 'to_user', 'status', 'created_at')
    list_filter = ('status',)


@admin.register(Friendship)
class FriendshipAdmin(admin.ModelAdmin):
    list_display = ('user_a', 'user_b', 'created_at')
    search_fields = ('user_a__username', 'user_b__username')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'recipient', 'created_at', 'read')
    readonly_fields = ('created_at',)
    fields = ('sender', 'recipient', 'content', 'image', 'audio', 'read', 'created_at')
    search_fields = ('sender__username', 'recipient__username', 'content')
    list_filter = ('read',)


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'created_at')
    search_fields = ('name', 'owner__username')


@admin.register(GroupMembership)
class GroupMembershipAdmin(admin.ModelAdmin):
    list_display = ('group', 'user', 'role', 'joined_at')
    search_fields = ('group__name', 'user__username')


@admin.register(GroupMessage)
class GroupMessageAdmin(admin.ModelAdmin):
    list_display = ('group', 'sender', 'created_at')
    search_fields = ('group__name', 'sender__username', 'content')


@admin.register(User)
class DevUserAdmin(UserAdmin):
    """User admin with a development-only 'Login as' action to impersonate a user for testing.

    This action is only enabled when `settings.DEBUG` is True.
    Use with caution — only for local/dev environments.
    """
    actions = ['login_as_selected']

    def login_as_selected(self, request, queryset):
        if not settings.DEBUG:
            self.message_user(request, 'Akcja dostępna tylko w trybie developerskim.', level=messages.ERROR)
            return
        if not request.user.is_staff:
            self.message_user(request, 'Brak uprawnień.', level=messages.ERROR)
            return
        user = queryset.first()
        if not user:
            self.message_user(request, 'Wybierz użytkownika.', level=messages.WARNING)
            return
        # perform login as the selected user
        auth_login(request, user)
        self.message_user(request, f'Zalogowano jako {user.username}.', level=messages.INFO)
        return redirect('profile', username=user.username)

    login_as_selected.short_description = 'Zaloguj jako wybranego użytkownika (dev only)'





