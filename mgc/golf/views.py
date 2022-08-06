from curses.ascii import HT
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse
from .models import User, Course, Hole

# Create your views here.
def index(request):
    return render(request, "golf/index.html")


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse('index'))
        else:
            return render(request, "golf/login.html", {
                "message": "Invalid username and/or password."
            })
    else: 
        return render(request, "golf/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse('index'))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]
        first_name = request.POST["first_name"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "golf/register.html", {
                "message": "Passwords must match."
            })
        
        # Attempt to create a new user
        try:
            user = User.objects.create_user(username, email, password)
            user.first_name = first_name
            user.save()
        except IntegrityError:
            return render(request, "golf/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse('index'))
    else:
        return render(request, "golf/register.html")


def post(request):
    """Allows the user to post a round or match. This route defaults to Manchester Country Club without altering the URL"""

    # Provide option drop down menu to switch course
    courses = Course.objects.all()
    course_names = []
    for course in courses:
        if course.name not in course_names:
            course_names.append(course.name)
    
    # Get default course information (MCC)
    default_course = Course.objects.get(pk=1)

    # Provide option drop down menu to switch tees
    available_courses = Course.objects.filter(name=default_course.name)
    available_tees = []
    for i in range(len(available_courses)):
        available_tees.append(available_courses[i].tees)
    
    # Get the hole information for this course
    holes = Hole.objects.filter(course=default_course)
    yardages = []
    handicaps = []
    pars = []
    for i in range(len(holes)):
        yardages.append(holes[i].yardage)
        handicaps.append(holes[i].handicap)
        pars.append(holes[i].par)
    golfers = User.objects.exclude(pk=1) # Provide option drop down menu to switch golfer
    context = {"course_length": range(1, 10), "course_names": course_names, 'golfers': golfers, 'default_course': default_course,'yardages': yardages, 'handicaps': handicaps, 'pars': pars, 'available_tees': available_tees}
    return render(request, "golf/post.html", context)


def post_course(request, name):
    """Allows the user to post a round or match. This route ensures we default to White tees if possible"""
    
    # Check if the requested course has more than one tee option
    courses = Course.objects.filter(name=name)
    if len(courses) == 1:
        tees = courses[0].tees 
        url = reverse('post_tees', kwargs={'name': name, 'tees': tees})
        return HttpResponseRedirect(url) # Defaults to only tee option
    else:
        # Default to White tees
        for i in range(len(courses)):
            if courses[i].tees == 'White':
                url = reverse('post_tees', kwargs={'name': name, 'tees': 'White'})
                return HttpResponseRedirect(url)
        # Otherwise choose any non white tee
        url = reverse('post_tees', kwargs={'name': name, 'tees': courses[0].tees})
        return HttpResponseRedirect(url) 


def post_tees(request, name, tees):
    if request.method == "GET":
        # Provide option to switch course
        courses = Course.objects.all()
        course_names = []
        for course in courses:
            if course.name not in course_names:
                course_names.append(course.name)
        index = course_names.index(f'{name}')
        course_names.insert(0, course_names.pop(index)) # Default to the requested course

        # Get selected course information
        default_course = Course.objects.get(name=name, tees=tees)
        
        # Check if we need to give options for other tees at this course
        available_courses = Course.objects.filter(name=name)
        available_tees = []
        for i in range(len(available_courses)):
            available_tees.append(available_courses[i].tees)
        index = available_tees.index(f'{tees}')
        available_tees.insert(0, available_tees.pop(index)) # Default to requested tees
        
        holes = Hole.objects.filter(course=default_course)
        yardages = []
        handicaps = []
        pars = []
        for i in range(len(holes)):
            yardages.append(holes[i].yardage)
            handicaps.append(holes[i].handicap)
            pars.append(holes[i].par)
        golfers = User.objects.exclude(pk=1)
        context = {"course_length": range(1, 10), "course_names": course_names, 'golfers': golfers, 'default_course': default_course,'yardages': yardages, 'handicaps': handicaps, 'pars': pars, 'available_tees': available_tees}
        return render(request, "golf/post.html", context)
    else:
        pass
