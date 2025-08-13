"""
ASGI config for DiaryInfoRealizeSystem project.

HTTP-only ASGI application (Channels removed to simplify stack).
"""

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DiaryInfoRealizeSystem.settings')

application = get_asgi_application()
