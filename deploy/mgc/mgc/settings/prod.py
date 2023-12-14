from .base import *
import os

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
DEBUG = False
ALLOWED_HOSTS = ['localhost', '137.184.45.38',
                 'oldmanchestergolfclub.com', 'www.oldmanchestergolfclub.com']
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
