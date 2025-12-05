
from django.shortcuts import render, redirect, get_object_or_404
import os
import time
import json
from django.urls import reverse
from django.contrib.auth import login, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib.auth import logout, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.http import JsonResponse
import traceback

from .models import Post, Profile
from django.db.models import Q
from .forms import RegistationForm, ProfileForm, PostForm
from .models import Message
from django.conf import settings

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
        try:
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
                    tb = traceback.format_exc()
                    print('DEBUG: avatar direct save failed ->', e)
                    print(tb)
                    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                        return JsonResponse({'success': False, 'error': str(e), 'traceback': tb}, status=500)
                    # fall through to render with messages
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
                    try:
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
                    except Exception as e:
                        tb = traceback.format_exc()
                        print('DEBUG: profile_form.save failed ->', e)
                        print(tb)
                        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                            return JsonResponse({'success': False, 'error': str(e), 'traceback': tb}, status=500)
                        # otherwise let rendering continue and show messages
        except Exception as e:
            tb = traceback.format_exc()
            print('DEBUG: unexpected error in change_avatar handler ->', e)
            print(tb)
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': str(e), 'traceback': tb}, status=500)

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


@login_required
def znajomi_view(request):
    """Show a list of other users with their profile summary."""
    # Build friends list (accepted friendships) and incoming friend requests
    friends = []
    incoming = []
    try:
        from .models import Friendship, FriendRequest
        # friendships where request.user is involved
        from django.db.models import Q as _Q
        fqs = Friendship.objects.filter(_Q(user_a=request.user) | _Q(user_b=request.user)).select_related('user_a', 'user_b')
        for f in fqs:
            other = f.user_b if f.user_a == request.user else f.user_a
            avatar_url = None
            try:
                if hasattr(other, 'profile') and other.profile.avatar:
                    try:
                        mtime = int(os.path.getmtime(other.profile.avatar.path))
                    except Exception:
                        mtime = int(time.time())
                    avatar_url = f"{other.profile.avatar.url}?v={mtime}"
            except Exception:
                avatar_url = None
            friends.append({'username': other.username, 'full_name': f"{other.first_name} {other.last_name}".strip(), 'avatar_url': avatar_url, 'bio': getattr(getattr(other, 'profile', None), 'bio', '')})

        # incoming pending friend requests
        reqs = FriendRequest.objects.filter(to_user=request.user, status=FriendRequest.STATUS_PENDING).select_related('from_user')
        for r in reqs:
            u = r.from_user
            avatar_url = None
            try:
                if hasattr(u, 'profile') and u.profile.avatar:
                    try:
                        mtime = int(os.path.getmtime(u.profile.avatar.path))
                    except Exception:
                        mtime = int(time.time())
                    avatar_url = f"{u.profile.avatar.url}?v={mtime}"
            except Exception:
                avatar_url = None
            incoming.append({'id': r.id, 'username': u.username, 'full_name': f"{u.first_name} {u.last_name}".strip(), 'avatar_url': avatar_url, 'bio': getattr(getattr(u, 'profile', None), 'bio', '')})
    except Exception:
        # Fallback: show all other users as entries (previous behaviour)
        users = User.objects.exclude(id=request.user.id).select_related()
        profiles = Profile.objects.filter(user__in=users).select_related('user')
        for p in profiles:
            avatar_url = None
            if p.avatar:
                try:
                    mtime = int(os.path.getmtime(p.avatar.path))
                except Exception:
                    mtime = int(time.time())
                avatar_url = f"{p.avatar.url}?v={mtime}"
            friends.append({
                'username': p.user.username,
                'full_name': f"{p.user.first_name} {p.user.last_name}".strip(),
                'avatar_url': avatar_url,
                'bio': p.bio,
            })

    return render(request, 'core/znajomi.html', {'friends': friends, 'incoming': incoming})


@login_required
def find_friends(request):
    q = request.GET.get('q', '').strip()
    entries = []
    suggestions = []
    if q:
        # search username, first_name, last_name
        users = User.objects.filter(
            Q(username__icontains=q) |
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q)
        ).exclude(id=request.user.id)
        profiles = Profile.objects.filter(user__in=users).select_related('user')
        for p in profiles:
            avatar_url = None
            if p.avatar:
                try:
                    mtime = int(os.path.getmtime(p.avatar.path))
                except Exception:
                    mtime = int(time.time())
                avatar_url = f"{p.avatar.url}?v={mtime}"
            entries.append({
                'username': p.user.username,
                'full_name': f"{p.user.first_name} {p.user.last_name}".strip(),
                'avatar_url': avatar_url,
                'bio': p.bio,
            })
    # Suggested users: show a few other recent users or random ones
    try:
        suggested_qs = Profile.objects.exclude(user=request.user).select_related('user')
        # exclude any already in entries
        found_usernames = {e['username'] for e in entries}
        if found_usernames:
            suggested_qs = suggested_qs.exclude(user__username__in=found_usernames)
        # prefer newest users first, fallback to random if few
        suggested_qs = suggested_qs.order_by('-user__date_joined')[:8]
        for p in suggested_qs:
            avatar_url = None
            if p.avatar:
                try:
                    mtime = int(os.path.getmtime(p.avatar.path))
                except Exception:
                    mtime = int(time.time())
                avatar_url = f"{p.avatar.url}?v={mtime}"
            suggestions.append({
                'username': p.user.username,
                'full_name': f"{p.user.first_name} {p.user.last_name}".strip(),
                'avatar_url': avatar_url,
                'bio': p.bio,
            })
    except Exception:
        suggestions = []

    return render(request, 'core/find_friends.html', {'entries': entries, 'query': q, 'suggestions': suggestions})


@login_required
def zdjecia_view(request):
    """Simple view to render the user's photos page."""
    # Collect images for the gallery: profile avatar + post images
    profile = Profile.objects.get(user=request.user)
    images = []
    # include profile avatar first if present
    if profile.avatar:
        try:
            mtime = int(os.path.getmtime(profile.avatar.path))
        except Exception:
            mtime = int(time.time())
        images.append({
            'url': f"{profile.avatar.url}?v={mtime}",
            'caption': 'Zdjęcie profilowe',
            'type': 'avatar',
        })

    # include post images (most recent first)
    post_images = Post.objects.filter(author=request.user).exclude(image__isnull=True).exclude(image__exact='').order_by('-created_at')
    for p in post_images:
        if p.image:
            try:
                mtime = int(os.path.getmtime(p.image.path))
            except Exception:
                mtime = int(time.time())
            images.append({
                'url': f"{p.image.url}?v={mtime}",
                'caption': p.content[:140] if p.content else 'Zdjęcie',
                'type': 'post',
                'post_id': p.id,
                'created_at': p.created_at,
            })

    return render(request, 'core/zdjecia.html', {'images': images, 'profile': profile})


@login_required
def informacje_view(request):
    """Render the information/about profile page."""
    # show information about the currently logged-in user
    profile = Profile.objects.get(user=request.user)
    avatar_url = None
    if profile.avatar:
        try:
            mtime = int(os.path.getmtime(profile.avatar.path))
        except Exception:
            mtime = int(time.time())
        avatar_url = f"{profile.avatar.url}?v={mtime}"
    return render(request, 'core/informacje.html', {
        'profile': profile,
        'avatar_url': avatar_url,
    })


@login_required
def send_friend_request(request, username):
    """Send a friend request to another user (simple placeholder).

    This is a lightweight implementation that does not create a Friendship
    model yet — it simply validates the target user and shows a message.
    Later we can replace this with a full friend-request workflow.
    """
    if request.user.username == username:
        messages.warning(request, 'Nie możesz wysłać zaproszenia do samego siebie.')
        return redirect('profile', username=username)

    target = get_object_or_404(User, username=username)

    # Create or update a FriendRequest if model exists
    try:
        from .models import FriendRequest
        if request.user == target:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Nie możesz wysłać zaproszenia do samego siebie.'}, status=400)
            messages.warning(request, 'Nie możesz wysłać zaproszenia do samego siebie.')
            return redirect('profile', username=username)

        fr, created = FriendRequest.objects.get_or_create(from_user=request.user, to_user=target,
                                                          defaults={'status': FriendRequest.STATUS_PENDING})
        if created:
            msg = f'Wysłano zaproszenie do {target.username}.'
        else:
            if fr.status == FriendRequest.STATUS_PENDING:
                msg = f'Zaproszenie do {target.username} jest już oczekujące.'
            elif fr.status == FriendRequest.STATUS_ACCEPTED:
                msg = f'Jesteście już znajomymi z {target.username}.'
            else:
                fr.status = FriendRequest.STATUS_PENDING
                fr.save(update_fields=['status'])
                msg = f'Wysłano ponownie zaproszenie do {target.username}.'

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'created': created, 'message': msg, 'fr_id': fr.id})
        messages.info(request, msg)
    except Exception:
        # If FriendRequest model doesn't exist or something went wrong, fallback to placeholder message
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Nie udało się wysłać zaproszenia.'}, status=500)
        messages.success(request, f'Wysłano zaproszenie do {target.username} (symulacja).')

    return redirect('profile', username=target.username)


@login_required
def accept_friend_request(request, fr_id):
    from .models import FriendRequest
    fr = get_object_or_404(FriendRequest, id=fr_id)
    if fr.to_user != request.user:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Not authorized'}, status=403)
        messages.error(request, 'Brak uprawnień.');
        return redirect('znajomi')

    # Accept the friend request
    fr.accept()
    # build friend info for AJAX
    other = fr.from_user
    avatar_url = None
    try:
        if hasattr(other, 'profile') and other.profile.avatar:
            try:
                mtime = int(os.path.getmtime(other.profile.avatar.path))
            except Exception:
                mtime = int(time.time())
            avatar_url = f"{other.profile.avatar.url}?v={mtime}"
    except Exception:
        avatar_url = None

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'friend': {'username': other.username, 'full_name': f"{other.first_name} {other.last_name}".strip(), 'avatar_url': avatar_url}})

    messages.success(request, f'Zaakceptowano zaproszenie od {other.username}.')
    return redirect('znajomi')


@login_required
def decline_friend_request(request, fr_id):
    from .models import FriendRequest
    fr = get_object_or_404(FriendRequest, id=fr_id)
    if fr.to_user != request.user:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Not authorized'}, status=403)
        messages.error(request, 'Brak uprawnień.');
        return redirect('znajomi')

    fr.decline()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    messages.info(request, 'Odrzucono zaproszenie.');
    return redirect('znajomi')


@login_required
def unfriend_user(request, username):
    # Remove an existing friendship between request.user and username
    target = get_object_or_404(User, username=username)
    try:
        from .models import Friendship
        # find ordered pair
        a, b = (request.user, target) if request.user.id < target.id else (target, request.user)
        deleted, _ = Friendship.objects.filter(user_a=a, user_b=b).delete()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        messages.success(request, f'Usunięto {target.username} z listy znajomych.')
    except Exception:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Nie udało się usunąć znajomego'}, status=500)
        messages.error(request, 'Wystąpił błąd przy usuwaniu znajomego.')
    return redirect('znajomi')


@login_required
def friend_requests_view(request):
    """Show incoming and outgoing friend requests separately."""
    from .models import FriendRequest
    incoming_qs = FriendRequest.objects.filter(to_user=request.user).order_by('-created_at').select_related('from_user')
    outgoing_qs = FriendRequest.objects.filter(from_user=request.user).order_by('-created_at').select_related('to_user')

    incoming = []
    for r in incoming_qs:
        u = r.from_user
        avatar_url = None
        try:
            if hasattr(u, 'profile') and u.profile.avatar:
                try:
                    mtime = int(os.path.getmtime(u.profile.avatar.path))
                except Exception:
                    mtime = int(time.time())
                avatar_url = f"{u.profile.avatar.url}?v={mtime}"
        except Exception:
            avatar_url = None
        incoming.append({'id': r.id, 'username': u.username, 'full_name': f"{u.first_name} {u.last_name}".strip(), 'avatar_url': avatar_url, 'status': r.status, 'created_at': r.created_at})

    outgoing = []
    for r in outgoing_qs:
        u = r.to_user
        avatar_url = None
        try:
            if hasattr(u, 'profile') and u.profile.avatar:
                try:
                    mtime = int(os.path.getmtime(u.profile.avatar.path))
                except Exception:
                    mtime = int(time.time())
                avatar_url = f"{u.profile.avatar.url}?v={mtime}"
        except Exception:
            avatar_url = None
        outgoing.append({'id': r.id, 'username': u.username, 'full_name': f"{u.first_name} {u.last_name}".strip(), 'avatar_url': avatar_url, 'status': r.status, 'created_at': r.created_at})

    return render(request, 'core/friend_requests.html', {'incoming': incoming, 'outgoing': outgoing})


@login_required
def friend_requests_count(request):
    from .models import FriendRequest
    cnt = FriendRequest.objects.filter(to_user=request.user, status=FriendRequest.STATUS_PENDING).count()
    return JsonResponse({'count': cnt})


@login_required
def cancel_friend_request(request, fr_id):
    """Allow a requester to cancel their outgoing pending friend request."""
    if request.method != 'POST' and request.headers.get('x-requested-with') != 'XMLHttpRequest':
        return redirect('friend_requests')
    from .models import FriendRequest
    try:
        fr = FriendRequest.objects.get(id=fr_id, from_user=request.user, status=FriendRequest.STATUS_PENDING)
        fr.delete()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'Anulowano zaproszenie.'})
        messages.info(request, 'Anulowano zaproszenie.')
        return redirect('friend_requests')
    except FriendRequest.DoesNotExist:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Zaproszenie nie istnieje lub nie masz do niego dostępu.'}, status=404)
        messages.error(request, 'Zaproszenie nie istnieje lub nie masz do niego dostępu.')
        return redirect('friend_requests')


@login_required
def friends_status_view(request):
    """List all users with friendship status relative to the current user.

    Status values: 'friends', 'pending_sent', 'pending_received', 'not_friends', 'unknown'
    """
    from .models import FriendRequest, Friendship
    users = User.objects.exclude(id=request.user.id).order_by('username')
    entries = []
    for u in users:
        status = 'not_friends'
        fr_id = None
        try:
            if Friendship.are_friends(request.user, u):
                status = 'friends'
            else:
                outgoing = FriendRequest.objects.filter(from_user=request.user, to_user=u, status=FriendRequest.STATUS_PENDING).first()
                incoming = FriendRequest.objects.filter(from_user=u, to_user=request.user, status=FriendRequest.STATUS_PENDING).first()
                if outgoing:
                    status = 'pending_sent'
                    fr_id = outgoing.id
                elif incoming:
                    status = 'pending_received'
                    fr_id = incoming.id
                else:
                    status = 'not_friends'
        except Exception:
            status = 'unknown'
        entries.append({'user': u, 'status': status, 'fr_id': fr_id})

    return render(request, 'core/friends_status.html', {'entries': entries})


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


@login_required
def chat_list(request):
    """Show list of friends you can chat with."""
    entries = []
    try:
        from .models import Friendship
        fqs = Friendship.objects.filter(Q(user_a=request.user) | Q(user_b=request.user)).select_related('user_a', 'user_b')
        for f in fqs:
            other = f.user_b if f.user_a == request.user else f.user_a
            avatar_url = None
            try:
                if hasattr(other, 'profile') and other.profile.avatar:
                    try:
                        mtime = int(os.path.getmtime(other.profile.avatar.path))
                    except Exception:
                        mtime = int(time.time())
                    avatar_url = f"{other.profile.avatar.url}?v={mtime}"
            except Exception:
                avatar_url = None
            entries.append({'username': other.username, 'full_name': f"{other.first_name} {other.last_name}".strip(), 'avatar_url': avatar_url})
    except Exception:
        entries = []
    return render(request, 'core/chat_list.html', {'entries': entries})


@login_required
def chat_room(request, username):
    """Chat room between request.user and username (must be friends)."""
    other = get_object_or_404(User, username=username)
    # ensure friendship exists
    try:
        from .models import Friendship
        if not Friendship.are_friends(request.user, other):
            messages.error(request, 'Nie macie połączenia znajomości. Nie można rozpocząć czatu.')
            return redirect('chat_list')
    except Exception:
        messages.error(request, 'Czat tymczasowo niedostępny.')
        return redirect('chat_list')

    # load recent messages (last 100)
    msgs = Message.objects.filter(
        Q(sender=request.user, recipient=other) | Q(sender=other, recipient=request.user)
    ).order_by('-created_at')[:100]
    msgs = list(reversed(msgs))
    return render(request, 'core/chat_room.html', {'other': other, 'messages': msgs})


@login_required
def send_message(request, username):
    """AJAX endpoint to send a message to a friend."""
    if request.method != 'POST' or request.headers.get('x-requested-with') != 'XMLHttpRequest':
        return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)
    other = get_object_or_404(User, username=username)
    try:
        from .models import Friendship
        if not Friendship.are_friends(request.user, other):
            return JsonResponse({'success': False, 'error': 'Not friends'}, status=403)
    except Exception:
        return JsonResponse({'success': False, 'error': 'Chat unavailable'}, status=500)
    try:
        # Support JSON body and multipart/form-data (for image/audio upload)
        content = ''
        img = None
        audio = None
        if request.content_type and request.content_type.startswith('multipart/'):
            # FormData submission
            content = request.POST.get('content', '').strip()
            img = request.FILES.get('image')
            audio = request.FILES.get('audio')
        else:
            data = json.loads(request.body.decode('utf-8') or '{}')
            content = data.get('content', '').strip()

        if not content and not img and not audio:
            return JsonResponse({'success': False, 'error': 'Empty message'}, status=400)

        m = Message(sender=request.user, recipient=other, content=content)
        if img:
            m.image = img
        if audio:
            m.audio = audio
        m.save()

        msg_data = {'id': m.id, 'sender': m.sender.username, 'content': m.content, 'created_at': m.created_at.isoformat()}
        if m.image:
            try:
                mtime = int(os.path.getmtime(m.image.path))
            except Exception:
                mtime = int(time.time())
            msg_data['image_url'] = f"{m.image.url}?v={mtime}"
        if getattr(m, 'audio', None):
            try:
                mtime = int(os.path.getmtime(m.audio.path))
            except Exception:
                mtime = int(time.time())
            msg_data['audio_url'] = f"{m.audio.url}?v={mtime}"

        return JsonResponse({'success': True, 'message': msg_data})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def fetch_messages(request, username):
    """AJAX endpoint to fetch messages for a chat; optional `after_id` GET param to fetch only newer msgs."""
    other = get_object_or_404(User, username=username)
    try:
        from .models import Friendship
        if not Friendship.are_friends(request.user, other):
            return JsonResponse({'success': False, 'error': 'Not friends'}, status=403)
    except Exception:
        return JsonResponse({'success': False, 'error': 'Chat unavailable'}, status=500)

    after_id = request.GET.get('after_id')
    qs = Message.objects.filter(Q(sender=request.user, recipient=other) | Q(sender=other, recipient=request.user)).order_by('created_at')
    if after_id:
        try:
            after_id = int(after_id)
            qs = qs.filter(id__gt=after_id)
        except ValueError:
            pass
    msgs = []
    for m in qs:
        item = {'id': m.id, 'sender': m.sender.username, 'content': m.content, 'created_at': m.created_at.isoformat()}
        if getattr(m, 'image', None):
            try:
                mtime = int(os.path.getmtime(m.image.path))
            except Exception:
                mtime = int(time.time())
            item['image_url'] = f"{m.image.url}?v={mtime}"
        if getattr(m, 'audio', None):
            try:
                mtime = int(os.path.getmtime(m.audio.path))
            except Exception:
                mtime = int(time.time())
            item['audio_url'] = f"{m.audio.url}?v={mtime}"
        msgs.append(item)
    return JsonResponse({'success': True, 'messages': msgs})