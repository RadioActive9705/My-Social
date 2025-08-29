from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
# Create your models here.
class CustomUser(AbstractUser):
    pass

class Profile(models.Model):
    user   = models.OneToOneField(settings.AUTH_USER_MODEL,
                                  on_delete=models.CASCADE)
    bio    = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='avatars/',
                               null=True, blank=True)
    privacy_settings = models.JSONField(default=dict)

    def __str__(self):
        return self.user.username
    
class Post(models.Model):
    author     = models.ForeignKey(settings.AUTH_USER_MODEL,
                                   on_delete=models.CASCADE,
                                   related_name='posts')
    content    = models.TextField()
    image      = models.ImageField(upload_to='post_images/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.author.username}: {self.content[:20]}…"