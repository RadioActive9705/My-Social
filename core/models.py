from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.core.files.base import ContentFile
import os
from io import BytesIO
from PIL import Image
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

    def save(self, *args, **kwargs):
        # Call parent save first to ensure we have a file path
        super().save(*args, **kwargs)
        if self.avatar:
            try:
                img_path = self.avatar.path
                img = Image.open(img_path)
                # Convert to RGBA if necessary
                if img.mode not in ('RGB', 'RGBA'):
                    img = img.convert('RGB')
                # Crop to square centered
                width, height = img.size
                min_dim = min(width, height)
                left = (width - min_dim) // 2
                top = (height - min_dim) // 2
                right = left + min_dim
                bottom = top + min_dim
                img = img.crop((left, top, right, bottom))
                # Resize to 400x400
                img = img.resize((400, 400), Image.LANCZOS)
                # Save back to same path (overwrite). Preserve PNG if original was PNG.
                buffer = BytesIO()
                orig_name = self.avatar.name or ''
                _, ext = os.path.splitext(orig_name.lower())
                if ext == '.png':
                    img.save(buffer, format='PNG', optimize=True)
                else:
                    img.save(buffer, format='JPEG', quality=90)
                # overwrite stored file content
                self.avatar.save(self.avatar.name, ContentFile(buffer.getvalue()), save=False)
                buffer.close()
                super().save(update_fields=['avatar'])
            except Exception as e:
                # If Pillow is not available or processing fails, keep original
                print('Avatar processing failed:', e)
    
class Post(models.Model):
    author     = models.ForeignKey(settings.AUTH_USER_MODEL,
                                   on_delete=models.CASCADE,
                                   related_name='posts')
    content    = models.TextField()
    image      = models.ImageField(upload_to='post_images/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.author.username}: {self.content[:20]}…"