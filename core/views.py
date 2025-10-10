
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth import login, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib.auth import logout, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages

from .models import Post, Profile
from .forms import RegistationForm, ProfileForm, PostForm

# Pobierz model użytkownika, który jest aktualnie aktywny w projekcie
User = get_user_model()

@login_required
def ustawienia_view(request):
    password_form = PasswordChangeForm(request.user, request.POST if 'change_password' in request.POST else None)
    email_changed = False
    avatar_changed = False
    profile = Profile.objects.get(user=request.user)
    profile_form = ProfileForm(request.POST or None, request.FILES or None, instance=profile)

    if request.method == 'POST' and 'change_password' in request.POST:
        if password_form.is_valid():
            user = password_form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Hasło zostało zmienione.')

    if request.method == 'POST' and 'change_email' in request.POST:
        new_email = request.POST.get('new_email')
        if new_email:
            request.user.email = new_email
            request.user.save()
            email_changed = True
            messages.success(request, 'E-mail został zmieniony.')

    if request.method == 'POST' and 'change_avatar' in request.POST:
        if profile_form.is_valid():
            profile_form.save()
            avatar_changed = True
            messages.success(request, 'Zdjęcie profilowe zostało zmienione.')
        else:
            print("Avatar upload errors:", profile_form.errors)

    return render(request, 'core/ustawienia.html', {
        'password_form': password_form,
        'email_changed': email_changed,
        'profile_form': profile_form,
        'avatar_changed': avatar_changed,
        'profile': profile,
    })

def logout_view(request):
    logout(request)
    return render(request,'logout.html')  # Przekierowanie do strony logowania po wylogowaniu

class CustomLoginView(LoginView):
    template_name = 'core/login.html'

    def get_success_url(self):
        next_url = self.request.GET.get('next') or self.request.POST.get('next')
        if next_url:
            return next_url
        return reverse('profile', kwargs={'username': self.request.user.username})

@login_required
def profile_view(request, username):
    user = get_object_or_404(User, username=username)
    profile, created = Profile.objects.get_or_create(user=user)

    avatar_changed = False
    # Handle avatar change (from modal)
    if request.user == user and request.method == "POST" and 'change_avatar' in request.POST:
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            avatar_changed = True
            return redirect('profile', username=username)
    # Handle normal profile edit
    elif request.user == user and request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('profile', username=username)
    else:
        form = ProfileForm(instance=profile)

    context = {
        'profile': profile,
        'form': form,
        'user_profile': user,
        'avatar_changed': avatar_changed,
    }
    return render(request, 'core/Profile.html', context)


def my_profile_redirect(request):
    # Ten widok jest przydatny do linku "Mój profil"
    if request.user.is_authenticated:
        return redirect('profile', username=request.user.username)
    return redirect('login')

from django.contrib.auth.decorators import login_required

@login_required(login_url='/login/')
def add_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('postlist')
    else:
        form = PostForm()
    return render(request, 'core/add_post.html', {'form': form})

def edit_post(request):
    post_id = request.GET.get('id')
    post = get_object_or_404(Post, id=post_id, author=request.user)
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            return redirect('postlist')
    else:
        form = PostForm(instance=post)
    return render(request, 'core/edit_post.html', {'form': form, 'post': post})

def delete_post(request):
    post_id = request.GET.get('id')
    post = get_object_or_404(Post, id=post_id, author=request.user)
    if request.method == 'POST':
        post.delete()
        return redirect('postlist')
    return render(request, 'core/delete_post.html', {'post': post})
    
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
    login_url = '/login/'
    return render(request, 'core/postlist.html', {'posts': posts, 'login_url': login_url})