from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.register, name="register"),
    path("post/", views.post, name="post"),
    path("post/<str:name>/", views.post_course, name="post_course"),
    path("post/<str:name>/<str:tees>/", views.post_tees, name="post_tees"),
    path("new/", views.new, name="new"),
    path("golfer/<str:golfer>/", views.golfer, name="golfer"),
    path("courses/<str:course>/<str:tees>/<str:golfer>/",
         views.course, name="course"),
    path("vs/<str:golfer1>/<str:golfer2>/", views.vs, name="vs"),
    path("edit/<int:match_id>/", views.edit, name="edit"),
    path("api/getData", views.getData, name="getData"),
    path("api/home", views.api_home, name='api_home'),
    path("api/golfer/<str:golfer>/", views.api_golfer, name="api_golfer"),
    path("api/vs/<str:golfer1>/<str:golfer2>/", views.api_vs, name="api_vs"),
    path("api/courses/<str:course>/<str:tees>/<str:golfer>/", views.api_course, name="api_course"),
    path("api/coursedata/<str:course>/<str:tees>/", views.get_course_data, name="get-course-data")
]
