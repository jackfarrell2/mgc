from .base import *
import os

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
DEBUG = False
ALLOWED_HOSTS = ['localhost', '142.93.242.160',
                 'manchestergolfclub.com', 'www.manchestergolfclub.com']
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
