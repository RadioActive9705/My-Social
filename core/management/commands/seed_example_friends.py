from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from core.models import Profile
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import hashlib
from django.contrib.auth import get_user_model as _get_user_model


class Command(BaseCommand):
    help = 'Create example users and profiles for local development (example friends)'

    def handle(self, *args, **options):
        User = get_user_model()
        examples = [
            {'username': 'alice', 'first_name': 'Alice', 'last_name': 'Nowak', 'email': 'alice@example.com', 'bio': 'Lubi podróże i fotografię.'},
            {'username': 'bob', 'first_name': 'Bob', 'last_name': 'Kowalski', 'email': 'bob@example.com', 'bio': 'Programista Python i fan piłki nożnej.'},
            {'username': 'carla', 'first_name': 'Carla', 'last_name': 'Wiśniewska', 'email': 'carla@example.com', 'bio': 'Miłośniczka kotów i kawy.'},
            {'username': 'dan', 'first_name': 'Dan', 'last_name': 'Zieliński', 'email': 'dan@example.com', 'bio': 'Gitarzysta i podróżnik.'},
            {'username': 'eva', 'first_name': 'Eva', 'last_name': 'Nowicka', 'email': 'eva@example.com', 'bio': 'Fotograf i projektant UX.'},
        ]

        created = 0
        for u in examples:
            username = u['username']
            user, was_created = User.objects.get_or_create(username=username, defaults={
                'first_name': u.get('first_name', ''),
                'last_name': u.get('last_name', ''),
                'email': u.get('email', ''),
            })
            if was_created:
                user.set_password('password123')
                user.save()
                created += 1
                self.stdout.write(self.style.SUCCESS(f"Created user: {username} (password: password123)"))
            else:
                self.stdout.write(f"User already exists: {username}")

            # ensure Profile exists and set bio
            profile, p_created = Profile.objects.get_or_create(user=user)
            if u.get('bio'):
                profile.bio = u['bio']
                profile.save()
            # create a placeholder avatar image if none exists
            if not profile.avatar:
                try:
                    # create a simple colored image with initials
                    initials = (u.get('first_name','')[:1] or u.get('username','')[:1]).upper()
                    # deterministic color from username
                    h = hashlib.md5(username.encode('utf-8')).hexdigest()
                    color = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
                    size = 400
                    img = Image.new('RGB', (size, size), color)
                    draw = ImageDraw.Draw(img)
                    try:
                        font = ImageFont.truetype('arial.ttf', 160)
                    except Exception:
                        font = ImageFont.load_default()
                    try:
                        # Pillow >= 8: textbbox provides reliable bbox
                        bbox = draw.textbbox((0, 0), initials, font=font)
                        w = bbox[2] - bbox[0]
                        h_text = bbox[3] - bbox[1]
                    except Exception:
                        try:
                            # Fallback to font.getsize
                            w, h_text = font.getsize(initials)
                        except Exception:
                            # Last resort: textsize (older Pillow)
                            try:
                                w, h_text = draw.textsize(initials, font=font)
                            except Exception:
                                w, h_text = (size // 2, size // 2)
                    draw.text(((size - w) / 2, (size - h_text) / 2), initials, fill=(255,255,255), font=font)
                    buffer = BytesIO()
                    img.save(buffer, format='JPEG', quality=85)
                    buffer.seek(0)
                    fname = f'avatars/{username}.jpg'
                    profile.avatar.save(fname, ContentFile(buffer.read()), save=True)
                    buffer.close()
                    print(f'Created placeholder avatar for {username}')
                except Exception as e:
                    print('Failed to create placeholder avatar for', username, e)

        # Create example friend requests between seeded users
        try:
            User = _get_user_model()
            from core.models import FriendRequest
            # create a few sample invitations: alice -> bob (accepted), carla -> alice (pending), dan -> eva (pending)
            mapping = [
                ('alice', 'bob', FriendRequest.STATUS_ACCEPTED),
                ('carla', 'alice', FriendRequest.STATUS_PENDING),
                ('dan', 'eva', FriendRequest.STATUS_PENDING),
            ]
            for a, b, status in mapping:
                try:
                    ua = User.objects.filter(username=a).first()
                    ub = User.objects.filter(username=b).first()
                    if ua and ub:
                        fr, created = FriendRequest.objects.get_or_create(from_user=ua, to_user=ub,
                                                                          defaults={'status': status})
                        if not created:
                            fr.status = status
                            fr.save(update_fields=['status'])
                except Exception as e:
                    print('Failed to create friend request', a, b, e)
        except Exception:
            # If FriendRequest model or imports fail, skip gracefully
            pass

        self.stdout.write(self.style.SUCCESS(f"Seeding complete. Created {created} users."))
