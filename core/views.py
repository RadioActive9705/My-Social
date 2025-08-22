from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth import login, get_user_model # <-- Zmieniony import!
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib.auth import logout

from django.shortcuts import render


from .models import Post, Profile
from .forms import RegistationForm, ProfileForm # <-- Poprawiłem literówkę w RegistrationForm w kodzie niżej

# Pobierz model użytkownika, który jest aktualnie aktywny w projekcie
User = get_user_model()

def logout_view(request):
    logout(request)
    return render(request,'logout.html')  # Przekierowanie do strony logowania po wylogowaniu

class CustomLoginView(LoginView):
    template_name = 'core/login.html'
    
    def get_success_url(self):
        # Przekierowuje na profil zalogowanego użytkownika
        return reverse('profile', kwargs={'username': self.request.user.username})

@login_required
def profile_view(request, username):
    # Używamy get_user_model() (czyli naszego CustomUser) do pobrania użytkownika
    user = get_object_or_404(User, username=username)
    
    # Pobieramy profil powiązany z tym użytkownikiem
    # Użyj get_or_create, aby uniknąć błędu, jeśli profil jeszcze nie istnieje
    profile, created = Profile.objects.get_or_create(user=user)
    
    # Obsługa formularza do edycji profilu
    if request.user == user and request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('profile', username=username)
    else:
        form = ProfileForm(instance=profile)
        
    context = {
        'profile': profile,
        'form': form,
        'user_profile': user # Możesz przekazać też obiekt usera, jeśli potrzebujesz
    }
    return render(request, 'core/Profile.html', context)


def my_profile_redirect(request):
    # Ten widok jest przydatny do linku "Mój profil"
    if request.user.is_authenticated:
        return redirect('profile', username=request.user.username)
    return redirect('login')

def add_post(request):
    # Your logic here
    return render(request, 'core/add_post.html')

def edit_post(request):
    # Your logic here
    return render(request, 'core/edit_post.html')

def delete_post(request):
    # Your logic here
    return render(request, 'core/delete_post.html')
    
def register(request):
    if request.method == 'POST':
        # Sugeruję zmianę nazwy 'RegistationForm' na 'RegistrationForm' w forms.py
        form = RegistationForm(request.POST) 
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('postlist')
    else:
        form = RegistationForm()
    return render(request, 'core/register.html', {'form': form})

def post_list(request):
    posts = Post.objects.all().order_by('-created_at')
    return render(request, 'core/postlist.html', {'posts': posts})