from django.shortcuts import render, get_object_or_404
from django.shortcuts import render, redirect
from django.contrib.auth import login
from .models import Post
from .forms import RegistationForm
from .models import CustomUser,Profile
from .forms import ProfileForm 
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.urls import reverse
from django.contrib.auth.models import User

class CustomLoginView(LoginView):
    template_name='core/login.html'
    
    def get_success_url(self):
        return reverse('profile',kwargs={'username': self.request.user.username})

@login_required
def profile_view(request,username):
    user_obj =  get_object_or_404(User,username=username)
    
    context={
        'user_profile': user_obj
    }
    
    
    
    return render(request, 'core/Profile.html', context)


def my_profile_redirect(request):
    current_username = request.user.username
    
    return redirect('profile',username=current_username)
    

def postlist(request):
    return render(request,'core/postlist.html')
    pass

def register(request):
    if request.method == 'POST':
        form = RegistationForm(request.POST) 
        if form.is_valid():
            user = form.save()       # tworzy CustomUser
            login(request, user)     # automatyczne zalogowanie
            return redirect('postlist')  # lub inna strona startowa
    else:
        form = RegistationForm()
    return render(request, 'core/register.html', {'form': form})

def post_list(request):
    posts = Post.objects.all().order_by('-created_at')
    return render(request, 'core/postlist.html', {'posts': posts})
# Create your views here.

class CustomLoginView(LoginView):
    template_name = 'core/login.html'

    def get_success_url(self):
        return reverse('profile', kwargs={'username': self.request.user.username})

# @login_required
# def profile_view(request,username):
#     user=get_object_or_404(CustomUser,username=username)
    
#     profile=get_object_or_404(Profile,user=user)
    
#     if request.user == user and request.method =="POST":
#         form = ProfileForm(request.POST, request.FILES, instance=profile)
#         if form.is_valid():
#             form.save()
#             return redirect('profile', username =username)
#         else:
#             form = ProfileForm(instance=profile)
        
#         return render(request, 'core/Profile.html',{
#             'profile': profile,
#             'form': form
#         })
    
    
