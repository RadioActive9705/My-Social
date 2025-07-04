from django.urls import path
from django.contrib.auth import views as auth_views
from .views import post_list, register, profile_view,my_profile_redirect
from .views import CustomLoginView

urlpatterns = [
    path('',      post_list ,          name='postlist'),
    path('register/', register ,     name='register'),
    path('login/',     CustomLoginView.as_view(),             name='login'),
    path('logout/',     auth_views.LogoutView.as_view(
                           next_page='login'
                       ),             name='logout'),
    path('profile/',my_profile_redirect,name='my_profile'),
    path('profile/<str:username>/', profile_view, name='profile')
]