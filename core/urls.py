from django.urls import path
from django.contrib.auth import views as auth_views
from .views import post_list, register, profile_view,my_profile_redirect
from .views import CustomLoginView
from . import views
from .views import add_post, edit_post, delete_post
from django.conf import settings
from django.conf.urls.static import static



from .views import znajomi_view

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
    path('chat/', views.chat_list, name='chat_list'),
    path('chat/<str:username>/', views.chat_room, name='chat_room'),
    path('chat/<str:username>/send/', views.send_message, name='send_message'),
    path('chat/<str:username>/fetch/', views.fetch_messages, name='fetch_messages'),
    path('znajomi/szukaj/', views.find_friends, name='find_friends'),
    path('zdjecia/', views.zdjecia_view, name='zdjecia'),
    path('informacje/', views.informacje_view, name='informacje'),
    path('send_friend_request/<str:username>/', views.send_friend_request, name='send_friend_request'),
    path('znajomi/status/', views.friends_status_view, name='friends_status'),
    path('friend_request/accept/<int:fr_id>/', views.accept_friend_request, name='accept_friend_request'),
    path('friend_request/decline/<int:fr_id>/', views.decline_friend_request, name='decline_friend_request'),
    path('friend_request/cancel/<int:fr_id>/', views.cancel_friend_request, name='cancel_friend_request'),
    path('unfriend/<str:username>/', views.unfriend_user, name='unfriend_user'),
    path('znajomi/requests/', views.friend_requests_view, name='friend_requests'),
    path('notifications/friend_requests_count/', views.friend_requests_count, name='friend_requests_count'),
    path('ustawienia/', views.ustawienia_view, name='ustawienia'),
    path('debug/avatar/', views.avatar_debug, name='avatar_debug'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)