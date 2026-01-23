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
    phone_number = models.CharField(max_length=32, blank=True, null=True)

    def __str__(self):
        return self.user.username

    def is_visible_to(self, viewer):
        """Return True if this profile's content (posts/photos) should be visible to `viewer`.

        viewer may be an AnonymousUser or a User instance.
        Visibility levels:
        - 'public'  : everyone
        - 'friends' : only friends
        - 'private' : only owner
        """
        try:
            level = None
            ps = self.privacy_settings
            if isinstance(ps, dict):
                level = ps.get('level')
            elif isinstance(ps, str):
                level = ps
            if not level:
                level = 'public'
        except Exception:
            level = 'public'

        # owner always sees their own profile
        if viewer and getattr(viewer, 'is_authenticated', False) and viewer == self.user:
            return True

        if level == 'public':
            return True
        if level == 'friends':
            # anonymous or unauthenticated users are not friends
            if not getattr(viewer, 'is_authenticated', False):
                return False
            try:
                return Friendship.are_friends(viewer, self.user)
            except Exception:
                return False
        # private
        return False

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


class FriendRequest(models.Model):
    """Simple FriendRequest model for demo purposes.

    status: 'pending', 'accepted', 'declined'
    """
    STATUS_PENDING = 'pending'
    STATUS_ACCEPTED = 'accepted'
    STATUS_DECLINED = 'declined'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_ACCEPTED, 'Accepted'),
        (STATUS_DECLINED, 'Declined'),
    ]

    from_user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='friend_requests_sent', on_delete=models.CASCADE)
    to_user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='friend_requests_received', on_delete=models.CASCADE)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('from_user', 'to_user')

    def accept(self):
        from django.db import IntegrityError
        self.status = self.STATUS_ACCEPTED
        self.save(update_fields=['status'])
        # Create a Friendship record when a request is accepted
        try:
            Friendship.befriend(self.from_user, self.to_user)
        except Exception:
            # ignore friendship creation errors
            pass

    def decline(self):
        self.status = self.STATUS_DECLINED
        self.save(update_fields=['status'])

    def __str__(self):
        return f"{self.from_user.username} -> {self.to_user.username} ({self.status})"


class Friendship(models.Model):
    """Symmetric friendship relation. We store user_a < user_b to keep uniqueness."""
    user_a = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='friendships_a', on_delete=models.CASCADE)
    user_b = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='friendships_b', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (('user_a', 'user_b'),)

    @classmethod
    def befriend(cls, u1, u2):
        # ensure consistent ordering
        if u1.id == u2.id:
            raise ValueError('Cannot befriend self')
        a, b = (u1, u2) if u1.id < u2.id else (u2, u1)
        obj, created = cls.objects.get_or_create(user_a=a, user_b=b)
        return obj

    @classmethod
    def are_friends(cls, u1, u2):
        a, b = (u1, u2) if u1.id < u2.id else (u2, u1)
        return cls.objects.filter(user_a=a, user_b=b).exists()

    def __str__(self):
        return f"{self.user_a.username} <-> {self.user_b.username}"


class Message(models.Model):
    """Simple direct message between two users.

    Messages are directional (sender -> recipient) and are stored with a timestamp.
    Only friends should be allowed to exchange messages in the UI/views.
    """
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='messages_sent', on_delete=models.CASCADE)
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='messages_received', on_delete=models.CASCADE)
    content = models.TextField()
    image = models.ImageField(upload_to='chat_images/', null=True, blank=True)
    audio = models.FileField(upload_to='chat_audio/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['sender', 'recipient', 'created_at']),
        ]

    def __str__(self):
        return f"{self.sender.username} -> {self.recipient.username} @ {self.created_at.isoformat()}"


class Group(models.Model):
    """A user-created group containing multiple members."""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='owned_groups', on_delete=models.CASCADE)
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='GroupMembership',
        related_name='groups_joined',
        related_query_name='groups_joined',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.owner.username})"


class GroupMembership(models.Model):
    """Membership record for a user in a group."""
    ROLE_MEMBER = 'member'
    ROLE_ADMIN = 'admin'
    ROLE_CHOICES = [
        (ROLE_MEMBER, 'Member'),
        (ROLE_ADMIN, 'Admin'),
    ]

    group = models.ForeignKey(Group, related_name='memberships', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='group_memberships', on_delete=models.CASCADE)
    role = models.CharField(max_length=16, choices=ROLE_CHOICES, default=ROLE_MEMBER)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (('group', 'user'),)

    def __str__(self):
        return f"{self.user.username} in {self.group.name} ({self.role})"


class GroupMessage(models.Model):
    """A message sent to a group."""
    group = models.ForeignKey(Group, related_name='messages', on_delete=models.CASCADE)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='group_messages_sent', on_delete=models.CASCADE)
    content = models.TextField(blank=True)
    image = models.ImageField(upload_to='chat_images/', null=True, blank=True)
    audio = models.FileField(upload_to='chat_audio/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['group', 'created_at']),
        ]

    def __str__(self):
        return f"{self.sender.username} -> #{self.group.name} @ {self.created_at.isoformat()}"


class FanPage(models.Model):
    """A simple fanpage owned by a user that others can follow."""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='owned_fanpages', on_delete=models.CASCADE)
    followers = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='followed_fanpages', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"FanPage: {self.name} ({self.owner.username})"