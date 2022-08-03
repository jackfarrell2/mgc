from django.urls import path
from . import views

# This is a test

urlpatterns = [
    path("", views.index, name="index")
]