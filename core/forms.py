from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Profile, Post, Friendship
from .models import Group, FanPage
from django.db.models import Q
from .models import Group
from django.contrib.auth.forms import PasswordResetForm as DjangoPasswordResetForm
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.contrib.auth.forms import AuthenticationForm

class RegistationForm(UserCreationForm):
    email=forms.EmailField(required=True)
    phone_number = forms.CharField(required=False, max_length=32,
                                   widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Numer telefonu (opcjonalnie)'}))
    
    class Meta:
        model=CustomUser
        fields =['username','email','password1','password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nazwa użytkownika'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'mail@przyklad.pl'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Hasło'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Powtórz hasło'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure all fields have Bootstrap classes even if widgets come from parent
        for fname in ('username', 'email', 'password1', 'password2'):
            field = self.fields.get(fname)
            if field:
                existing = field.widget.attrs.get('class', '')
                classes = (existing + ' form-control').strip()
                field.widget.attrs.update({'class': classes})
        # ensure phone_number has form-control as well
        if 'phone_number' in self.fields:
            self.fields['phone_number'].widget.attrs.update({'class': 'form-control'})
    
class ProfileForm(forms.ModelForm):
    PRIVACY_CHOICES = [
        ('public', 'Publiczne (wszyscy widzą)'),
        ('friends', 'Tylko znajomi'),
        ('private', 'Tylko ja'),
    ]

    # expose a simple choice widget while model keeps JSONField storage
    privacy_settings = forms.ChoiceField(choices=PRIVACY_CHOICES, required=False,
                                         widget=forms.Select(attrs={'class': 'form-select'}))

    class Meta:
        model = Profile
        fields = ['bio', 'avatar', 'privacy_settings', 'phone_number']
        widgets = {
            'avatar': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Numer telefonu'}),
        }

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance', None)
        super().__init__(*args, **kwargs)
        # initialize privacy field from existing JSON or string
        initial_value = 'public'
        if instance is not None:
            ps = getattr(instance, 'privacy_settings', None)
            if isinstance(ps, dict):
                initial_value = ps.get('level', initial_value)
            elif isinstance(ps, str):
                initial_value = ps
        self.fields['privacy_settings'].initial = initial_value

    def save(self, commit=True):
        inst = super().save(commit=False)
        val = self.cleaned_data.get('privacy_settings')
        if val:
            inst.privacy_settings = {'level': val}
        else:
            inst.privacy_settings = {'level': 'public'}
        if commit:
            inst.save()
        return inst

    def save_user_and_profile(self, request=None):
        """Save the User and create/update the related Profile with phone number."""
        user = self.save(commit=True)
        phone = self.cleaned_data.get('phone_number')
        try:
            profile, _ = Profile.objects.get_or_create(user=user)
            if phone:
                profile.phone_number = phone.strip()
            profile.save()
        except Exception:
            pass
        return user

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['content', 'image']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Napisz coś...'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


class UsernameOrEmailPasswordResetForm(DjangoPasswordResetForm):
    """Allow users to request a password reset by entering email OR username.

    This replaces the usual EmailField with a CharField so users can type
    either their email address or their username. We override `get_users`
    to look up users by email or username.
    """
    email = forms.CharField(label='E-mail lub nazwa użytkownika',
                            widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'E-mail lub nazwa użytkownika'}))

    def get_users(self, identifier):
        """Yield active users matching the given identifier (email or username)."""
        UserModel = get_user_model()
        if not identifier:
            return
        identifier = identifier.strip()
        qs = UserModel._default_manager.filter(
            Q(email__iexact=identifier) | Q(username__iexact=identifier)
        )
        for user in qs:
            if user.has_usable_password() and user.is_active:
                yield user


class UsernameOrEmailAuthenticationForm(AuthenticationForm):
    """Authentication form with placeholder explaining that email or username is accepted."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # customize username field widget
        if 'username' in self.fields:
            self.fields['username'].widget = forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nazwa użytkownika lub e-mail'
            })
        if 'password' in self.fields:
            self.fields['password'].widget = forms.PasswordInput(attrs={
                'class': 'form-control',
                'placeholder': 'Hasło'
            })


class GroupCreateForm(forms.Form):
    name = forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nazwa grupy'}))
    description = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Opis (opcjonalnie)'}))
    members = forms.ModelMultipleChoiceField(queryset=None, required=False,
                                             widget=forms.SelectMultiple(attrs={'class': 'form-select'}),
                                             help_text='Wybierz znajomych do dodania (opcjonalnie)')

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        # default members queryset: all users except the creator
        if user:
            # limit selectable members to user's friends for privacy
            try:
                # find friend user ids via Friendship table
                fq = Friendship.objects.filter(Q(user_a=user) | Q(user_b=user)).values_list('user_a', 'user_b')
                friend_ids = set()
                for a, b in fq:
                    if a == user.id:
                        friend_ids.add(b)
                    elif b == user.id:
                        friend_ids.add(a)
                qs = CustomUser.objects.filter(id__in=friend_ids)
            except Exception:
                qs = CustomUser.objects.exclude(id=user.id)
        else:
            qs = CustomUser.objects.all()
        self.fields['members'].queryset = qs


class GroupEditForm(forms.ModelForm):
    members = forms.ModelMultipleChoiceField(queryset=None, required=False,
                                             widget=forms.SelectMultiple(attrs={'class': 'form-select'}),
                                             help_text='Wybierz użytkowników przypisanych do grupy')

    class Meta:
        model = Group
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        group = kwargs.pop('group', None)
        super().__init__(*args, **kwargs)
        # limit members to friends (exclude owner)
        if user is not None:
            try:
                fq = Friendship.objects.filter(Q(user_a=user) | Q(user_b=user)).values_list('user_a', 'user_b')
                friend_ids = set()
                for a, b in fq:
                    if a == user.id:
                        friend_ids.add(b)
                    elif b == user.id:
                        friend_ids.add(a)
                qs = CustomUser.objects.filter(id__in=friend_ids)
            except Exception:
                qs = CustomUser.objects.exclude(id=user.id)
        else:
            qs = CustomUser.objects.all()
        self.fields['members'].queryset = qs
        # pre-select current members (excluding owner)
        if group is not None:
            current = [m.user_id for m in getattr(group, 'memberships').all() if m.user_id != getattr(group, 'owner_id', None)]
            self.fields['members'].initial = current


class FanPageForm(forms.ModelForm):
    class Meta:
        model = FanPage
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nazwa fanpage'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Opis (opcjonalnie)'}),
        }