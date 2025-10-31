from django.urls import path
from django.contrib.auth import views as auth_views
from .views import post_list, register, profile_view,my_profile_redirect
from .views import CustomLoginView
from . import views
from .views import add_post, edit_post, delete_post
from django.conf import settings
from django.conf.urls.static import static



from django.shortcuts import render

def znajomi_view(request):
    return render(request, 'core/znajomi.html')

def zdjecia_view(request):
    return render(request, 'core/zdjecia.html')

def informacje_view(request):
    return render(request, 'core/informacje.html')

urlpatterns = [
    path('',      post_list ,          name='postlist'),
    path('register/', register ,     name='register'),
    path('login/',     CustomLoginView.as_view(),name='login'),
    path('profile/',my_profile_redirect,name='my_profile'),
    path('profile/<str:username>/', profile_view, name='profile'),
    path('logout/', views.logout_view, name='logout'),
    path('add_post/', add_post, name='add_post'),
    path('edit_post/', edit_post, name='edit_post'),
    path('delete_post/', delete_post, name='delete_post'),
    path('znajomi/', znajomi_view, name='znajomi'),
    path('zdjecia/', zdjecia_view, name='zdjecia'),
    path('informacje/', informacje_view, name='informacje'),
    path('ustawienia/', views.ustawienia_view, name='ustawienia'),
    path('debug/avatar/', views.avatar_debug, name='avatar_debug'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)