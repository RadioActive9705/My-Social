from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser,Profile

class RegistationForm(UserCreationForm):
    email=forms.EmailField(required=True)
    
    class Meta:
        model=CustomUser
        fields =['username','email','password1','password2']
    
class ProfileForm(forms.ModelForm):
    class Meta:
        model=Profile
        fields=['bio','avatar','privacy_settings']