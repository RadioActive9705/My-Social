from django.urls import path
from django.contrib.auth import views as auth_views
from django.contrib.auth import views as auth_views
from .views import post_list, register, profile_view

urlpatterns = [
    path('',      post_list ,          name='postlist'),
    path('register/', register ,     name='register'),
    path('login/',      auth_views.LoginView.as_view(
                           template_name='core/login.html'
                       ),             name='login'),
    path('logout/',     auth_views.LogoutView.as_view(
                           next_page='login'
                       ),             name='logout'),
    path('profile/<str:username>', profile_view, name='profile')
]