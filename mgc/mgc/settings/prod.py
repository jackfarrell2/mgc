from .base import *
import os

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
DEBUG = False
ALLOWED_HOSTS = ['oldmanchestergolfclub.xyz', 'www.oldmanchestergolfclub.xyz']
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

CORS_ALLOWED_ORIGINS = [
    'https://manchestergolfclub.com',
    'https://www.manchestergolfclub.com',
]

CSRF_TRUSTED_ORIGINS=['https://*.oldmanchestergolfclub.xyz']
