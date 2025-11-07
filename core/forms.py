from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Profile, Post

class RegistationForm(UserCreationForm):
    email=forms.EmailField(required=True)
    
    class Meta:
        model=CustomUser
        fields =['username','email','password1','password2']
    
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