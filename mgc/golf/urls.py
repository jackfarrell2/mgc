from django.urls import path
from . import views


urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"), 
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("post/<str:name>", views.post_route, name="post_route"),
    path("post/<str:name>/<str:tees>", views.post, name="post"),   

]