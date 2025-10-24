
from django.shortcuts import render, redirect, get_object_or_404
import os
import time
from django.urls import reverse
from django.contrib.auth import login, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib.auth import logout, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.http import JsonResponse

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
        print('DEBUG: ustawienia_view POST keys:', list(request.POST.keys()))
        print('DEBUG: ustawienia_view FILES keys:', list(request.FILES.keys()))
        # If an avatar file was uploaded, assign it directly to the profile to avoid
        # requiring other form fields (privacy_settings) when only changing avatar.
        uploaded = request.FILES.get('avatar')
        if uploaded:
            try:
                print('DEBUG: direct-assign avatar file ->', uploaded.name)
                profile.avatar = uploaded
                profile.save()
                avatar_changed = True
                messages.success(request, 'Zdjęcie profilowe zostało zmienione.')
                # If this is an AJAX request, return JSON with the new avatar URL
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    try:
                        mtime = int(os.path.getmtime(profile.avatar.path))
                    except Exception:
                        mtime = int(time.time())
                    avatar_url = f"{profile.avatar.url}?v={mtime}"
                    return JsonResponse({'success': True, 'avatar_url': avatar_url, 'message': 'Zdjęcie zapisane.'})
                return redirect('ustawienia')
            except Exception as e:
                print('DEBUG: avatar direct save failed ->', e)
        else:
            is_valid = profile_form.is_valid()
            print('DEBUG: profile_form.is_valid ->', is_valid)
            if not is_valid:
                print('DEBUG: profile_form.errors ->', profile_form.errors)
            if is_valid:
                # show current avatar before save
                try:
                    print('DEBUG: before save, profile.avatar ->', getattr(profile, 'avatar'))
                except Exception as e:
                    print('DEBUG: before save avatar access error', e)
                profile_form.save()
                avatar_changed = True
                messages.success(request, 'Zdjęcie profilowe zostało zmienione.')
                try:
                    print('DEBUG: after save, profile.avatar ->', profile.avatar.name, profile.avatar.url)
                except Exception as e:
                    print('DEBUG: after save avatar access error', e)
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    try:
                        mtime = int(os.path.getmtime(profile.avatar.path))
                    except Exception:
                        mtime = int(time.time())
                    avatar_url = f"{profile.avatar.url}?v={mtime}"
                    return JsonResponse({'success': True, 'avatar_url': avatar_url, 'message': 'Zdjęcie zapisane.'})

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
        print('DEBUG: profile_view POST keys:', list(request.POST.keys()))
        print('DEBUG: profile_view FILES keys:', list(request.FILES.keys()))
        uploaded = request.FILES.get('avatar')
        if uploaded:
            try:
                print('DEBUG: profile direct-assign avatar ->', uploaded.name)
                profile.avatar = uploaded
                profile.save()
                avatar_changed = True
                return redirect('profile', username=username)
            except Exception as e:
                print('DEBUG: profile direct save failed ->', e)
        else:
            form = ProfileForm(request.POST, request.FILES, instance=profile)
            valid = form.is_valid()
            print('DEBUG: profile form is_valid ->', valid)
            if not valid:
                print('DEBUG: profile form errors ->', form.errors)
            if valid:
                try:
                    print('DEBUG: profile before save avatar ->', getattr(profile, 'avatar'))
                except Exception as e:
                    print('DEBUG: error reading profile.avatar before save', e)
                form.save()
                avatar_changed = True
                try:
                    print('DEBUG: profile after save avatar ->', profile.avatar.name, profile.avatar.url)
                except Exception as e:
                    print('DEBUG: error reading profile.avatar after save', e)
                return redirect('profile', username=username)
    # Handle normal profile edit
    elif request.user == user and request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('profile', username=username)
    else:
        form = ProfileForm(instance=profile)

    # Build an avatar URL with cache-busting query param based on file mtime
    avatar_url = None
    if profile.avatar:
        try:
            mtime = int(os.path.getmtime(profile.avatar.path))
        except Exception:
            mtime = int(time.time())
        avatar_url = f"{profile.avatar.url}?v={mtime}"

    context = {
        'profile': profile,
        'form': form,
        'user_profile': user,
        'avatar_changed': avatar_changed,
        'avatar_url': avatar_url,
    }
    return render(request, 'core/Profile.html', context)


@login_required
def avatar_debug(request):
    """Return simple debug info about the logged-in user's avatar."""
    profile = Profile.objects.get(user=request.user)
    info = {
        'avatar_field_name': None,
        'avatar_url': None,
        'avatar_path': None,
        'exists_on_disk': False,
        'mtime': None,
    }
    if profile.avatar:
        info['avatar_field_name'] = profile.avatar.name
        info['avatar_url'] = profile.avatar.url
        try:
            info['avatar_path'] = profile.avatar.path
            info['exists_on_disk'] = os.path.exists(profile.avatar.path)
            if info['exists_on_disk']:
                info['mtime'] = int(os.path.getmtime(profile.avatar.path))
        except Exception as e:
            info['error'] = str(e)
    return render(request, 'core/avatar_debug.html', {'info': info})


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