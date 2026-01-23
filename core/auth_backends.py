from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

UserModel = get_user_model()

class EmailOrUsernameModelBackend(ModelBackend):
    """Authenticate using either username or email address."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get('email') or kwargs.get('username')
        if username is None or password is None:
            return None
        try:
            user = UserModel.objects.filter(
                Q(username__iexact=username) | Q(email__iexact=username)
            ).distinct().get()
        except UserModel.DoesNotExist:
            return None
        except UserModel.MultipleObjectsReturned:
            # If multiple (shouldn't happen with unique constraints), prefer exact username match
            try:
                user = UserModel.objects.get(username__iexact=username)
            except Exception:
                return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
