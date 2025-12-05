from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Profile, Post

class RegistationForm(UserCreationForm):
    email=forms.EmailField(required=True)
    
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
    
class ProfileForm(forms.ModelForm):
    class Meta:
        model=Profile
        fields=['bio','avatar','privacy_settings']
        widgets = {
            'avatar': forms.ClearableFileInput(attrs={'class':'form-control'}),
            'bio': forms.Textarea(attrs={'class':'form-control', 'rows':4}),
            'privacy_settings': forms.Select(attrs={'class':'form-select'}),
        }

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['content', 'image']