
import os
import django
import json
import sys

# Setup Django - MUST BE DONE BEFORE IMPORTS
sys.path.append(r'c:\Users\2025\.gemini\antigravity\scratch\electoral_office')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "electoral_office.settings")
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import User
from elections.views import voter_lookup_ajax

# Create a request
factory = RequestFactory()
request = factory.get('/api/voter-lookup/?voter_number=100000010')

# Simulate logged-in user
# Using get_or_create to avoid errors if it exists
try:
    user, created = User.objects.get_or_create(username='testadmin', defaults={'email': 'test@example.com'})
    request.user = user
except Exception as e:
    print(f"User creation failed: {e}")
    # Try getting first user
    user = User.objects.first()
    if user:
        request.user = user
    else:
        print("No users found")
        sys.exit(1)

# Call the view
response = voter_lookup_ajax(request)

# Check response
print(f"Status Code: {response.status_code}")
content = json.loads(response.content.decode('utf-8'))
print(f"Content: {json.dumps(content, indent=2, ensure_ascii=False)}")
