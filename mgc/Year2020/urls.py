from cgitb import handler
from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="2020_index"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.register, name="register"),
    path("golfer/<str:golfer>/", views.golfer, name="2020_golfer"),
    path("courses/<str:course>/<str:tees>/<str:golfer>/",
         views.course, name="2020_course"),
    path("vs/<str:golfer1>/<str:golfer2>/", views.vs, name="2020_vs"),
]
