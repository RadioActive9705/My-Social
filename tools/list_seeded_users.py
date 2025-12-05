import os
import django
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysocial.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

seed_names = ['alice','bob','carla','dan','eva']
qs = User.objects.filter(username__in=seed_names).order_by('username')
if not qs.exists():
    print('No seeded users found.')
else:
    for u in qs:
        print(f'{u.username} | is_staff={u.is_staff} | date_joined={u.date_joined} | email={u.email}')
