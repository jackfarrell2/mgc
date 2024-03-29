from datetime import datetime
from django.db import IntegrityError
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse
from django.core.paginator import Paginator
from django.core.exceptions import ObjectDoesNotExist
from .models import User, Course, Score, Round, Hole
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from golf.helpers import delete_rounds, get_stats, get_scorecard, \
    get_course_avg_scorecard, get_vs_scorecards, add_course, \
    post_match, get_course_names, get_tee_options, get_course_info, \
    get_bart_birdies, api_add_course, api_stats, api_scorecards

# Regular views (API's below)


def index(request):
    """Show statistics for all golfers, excluding solo rounds"""
    # Gather statistics for golfers who have played rounds
    all_golfers = User.objects.filter(has_rounds=True)
    all_stats = []
    for golfer in all_golfers:
        # Exclude solo rounds
        golfers_rounds = Round.objects.filter(
            golfer=golfer, date__year=2023).exclude(solo_round=True)
        if len(golfers_rounds) > 0:
            stats = get_stats(golfers_rounds)
            all_stats.append(stats)

    # Sort stats by average score
    def avg_score(golfers_stats):
        return golfers_stats[2]
    all_stats.sort(key=avg_score)
    # Get bart birdies
    bart_birdies = get_bart_birdies()
    # Render template
    context = {'all_stats': all_stats, 'bart_birdies': bart_birdies}
    return render(request, "golf/index.html", context)


def golfer(request, golfer):
    """Shows a golfers rounds and statistics, including solo rounds"""
    # Get golfers statistics
    this_golfer = User.objects.get(first_name=golfer)
    golfer_rounds = Round.objects.filter(
        golfer=this_golfer, date__year=2023).order_by('-date')
    if len(golfer_rounds) > 0:
        stats = get_stats(golfer_rounds)
    else:
        message = 'The selected golfer has not played a round yet in this year'
        return render(request, "golf/error.html", {'message': message})
    # Only offer the option to switch to golfers that have played a round
    all_golfers = User.objects.filter(has_rounds=True).order_by('first_name')
    # Gather a scorecard for every round the golfer has played
    scorecards = []
    for this_round in golfer_rounds:
        scorecard = get_scorecard(this_round)
        scorecards.append(scorecard)
    # Paginate scorecards
    scorecards = Paginator(scorecards, 3)
    page_number = request.GET.get('page')
    this_page_scorecard = scorecards.get_page(page_number)
    # Render template
    context = {'stats': stats, 'scorecards': this_page_scorecard,
               'golfer': this_golfer, 'course_length': range(1, 10),
               'all_golfers': all_golfers}
    return render(request, "golf/golfer.html", context)


def course(request, course, tees, golfer):
    """Shows a golfers statistics, hole averages, and rounds on a course"""
    # Provide option to switch golfer and/or course
    all_golfers = User.objects.filter(has_rounds=True).order_by('first_name')
    course_names = get_course_names(course)
    tee_options = get_tee_options(course, tees)
    # Retrieve rounds that this golfer has played at this course
    course = Course.objects.get(name=course, tees=tees)
    golfer = User.objects.get(first_name=golfer)
    # Include solo rounds
    rounds = Round.objects.filter(golfer=golfer,
                                  course=course,
                                  date__year=2023).order_by('-date')
    # Ensure the golfer has played a round at this course
    if len(rounds) == 0:
        message = 'The selected golfer has not played the selected course'
        return render(request, "golf/error.html", {'message': message})
    # Retrieve a scorecard for every round
    scorecards = []
    for round in rounds:
        scorecard = get_scorecard(round)
        scorecards.append(scorecard)
    stats = get_stats(rounds)  # Retrieve stats for this golfer at this course
    # Retrieve golfers hole averages at this course
    avg_scorecard = get_course_avg_scorecard(rounds)
    # Paginate
    scorecards = Paginator(scorecards, 3)
    page_number = request.GET.get('page')
    this_page_scorecard = scorecards.get_page(page_number)
    # Render template
    context = {'stats': stats, 'avg_scorecard': avg_scorecard,
               'scorecards': this_page_scorecard, 'courses': course_names,
               'tees': tee_options, 'golfer': golfer,
               'course_length': range(1, 10), 'all_golfers': all_golfers}
    return render(request, "golf/course.html", context)


def vs(request, golfer1, golfer2):
    """Shows stats of one golfer vs another"""
    # Ensure two distinct golfers were selected
    if golfer1 == golfer2:
        message = "Must select two separate golfers."
        return render(request, "golf/error.html", {'message': message})
    # Offer option to switch to any golfer
    all_golfers = User.objects.filter(has_rounds=True).order_by('first_name')
    # Retrieve all rounds for selected golfers
    golfer_one = User.objects.get(first_name=golfer1)
    golfer_two = User.objects.get(first_name=golfer2)
    golfer_one_rounds = Round.objects.filter(
        golfer=golfer_one, date__year=2023)
    golfer_two_rounds = Round.objects.filter(
        golfer=golfer_two, date__year=2023)
    # Check both golfers have playes a round in 2023
    if len(golfer_one_rounds) == 0 or len(golfer_two_rounds) == 0:
        message = 'The selected golfers have not played each other.'
        return render(request, "golf/error.html", {'message': message})
    # Check which rounds are on the same scorecard / are a match
    golfer_one_match_ids = []
    golfer_two_match_ids = []
    # All golfer one matches
    for this_round in golfer_one_rounds:
        if this_round.match not in golfer_one_match_ids:
            golfer_one_match_ids.append(this_round.match)
    # All golfer two matches
    for this_round in golfer_two_rounds:
        if this_round.match not in golfer_two_match_ids:
            golfer_two_match_ids.append(this_round.match)
    # Find common matches
    cumulative_match_ids = []
    for id in golfer_one_match_ids:
        if id in golfer_two_match_ids:
            cumulative_match_ids.append(id)
    if len(cumulative_match_ids) == 0:
        message = 'The selected golfers have not played each other.'
        return render(request, "golf/error.html", {'message': message})
    # Retrieve golfer rounds that are a match between the two golfers
    golfer_one_rounds = \
        Round.objects.filter(golfer=golfer_one, date__year=2023,
                             match__in=cumulative_match_ids).order_by('-date')
    golfer_two_rounds = \
        Round.objects.filter(golfer=golfer_two, date__year=2023,
                             match__in=cumulative_match_ids).order_by('-date')
    # Get stats for both golfers
    golfer_one_stats = get_stats(golfer_one_rounds)
    golfer_two_stats = get_stats(golfer_two_rounds)
    # Get scorecards for each match
    both_golfers_rounds = [golfer_one_rounds, golfer_two_rounds]
    scorecards = get_vs_scorecards(both_golfers_rounds)
    # Calculate the records between the two golfers
    match_checker = {'golfer_one_wins': 0, 'golfer_two_wins': 0, 'ties': 0}
    for scorecard in scorecards:
        # Golfer one won this match
        if scorecard['strokes_one'][-1] < scorecard['strokes_two'][-1]:
            match_checker['golfer_one_wins'] += 1
        # Golfer two won this match
        elif scorecard['strokes_one'][-1] > scorecard['strokes_two'][-1]:
            match_checker['golfer_two_wins'] += 1
        # This match was a tie
        else:
            match_checker['ties'] += 1
    # Record wins and ties
    golfer_one_wins = match_checker['golfer_one_wins']
    golfer_two_wins = match_checker['golfer_two_wins']
    ties = match_checker['ties']
    # Message for golfer one winning or tie
    if golfer_one_wins >= golfer_two_wins:
        winner = f"{golfer_one} is {golfer_one_wins}"
        loser = f"-{golfer_two_wins}-{ties} vs {golfer_two}"
        record = winner + loser
    # Message for golfer two winning
    else:
        winner = f"{golfer_two} is {golfer_two_wins}"
        loser = f"-{golfer_one_wins}-{ties} vs {golfer_one}"
        record = winner + loser
    # Sort stats by which golfer has best average round
    if golfer_one_stats[2] > golfer_two_stats[2]:
        buffer = golfer_one_stats
        golfer_one_stats = golfer_two_stats
        golfer_two_stats = buffer
    # Paginate scorecards
    scorecards = Paginator(scorecards, 3)
    page_number = request.GET.get('page')
    this_page_scorecard = scorecards.get_page(page_number)
    # Render template
    context = {'stats_one': golfer_one_stats, 'stats_two': golfer_two_stats,
               'scorecards': this_page_scorecard,
               'course_length': range(1, 10), 'all_golfers': all_golfers,
               'golfer_one': golfer_one, 'golfer_two': golfer_two,
               'record': record}
    return render(request, "golf/vs.html", context)


def post(request):
    """Lets the user post a match. Default to MCC White Tees"""
    if request.method == "POST":
        # Post the match
        post_success_checker = post_match(request)
        # Success
        if post_success_checker[0]:
            # Return to home page
            return HttpResponseRedirect(reverse('index'))
        # Failure
        else:
            # Render failure template
            return render(request, "golf/error.html",
                          {'message': post_success_checker[1]})
    else:
        # Provide a form to post a match
        # Get default course information (MCC)
        default_course = Course.objects.get(pk=1)
        # Provide option to switch course
        course_names = get_course_names(default_course.name)
        # Provide option drop down menu to switch tees
        available_courses = Course.objects.filter(name=default_course.name)
        available_tees = []
        for i in range(len(available_courses)):
            available_tees.append(available_courses[i].tees)
        # Get course information for scorecard
        course_info = get_course_info(default_course)
        # Provide option drop down menu to switch golfer
        golfers = User.objects.exclude(pk=1).order_by('first_name')
        # Create default date as a placeholder date
        now = datetime.now()
        date = now.strftime("%Y-%m-%d")
        # Render template
        context = {"course_length": range(1, 10),
                   "course_names": course_names,
                   "golfers": golfers, "default_course": default_course,
                   "yardages": course_info[2], "handicaps": course_info[1],
                   'pars': course_info[0], "available_tees": available_tees,
                   "date": date}
        return render(request, "golf/post.html", context)


def post_course(request, name):
    """Allows the user to post a course. Default to white tees"""
    # Check if the requested course has more than one tee option
    courses = Course.objects.filter(name=name)
    if len(courses) == 1:
        tees = courses[0].tees
        url = reverse('post_tees', kwargs={'name': name, 'tees': tees})
        return HttpResponseRedirect(url)  # Defaults to only tee option
    else:
        # Default to White tees
        for i in range(len(courses)):
            if courses[i].tees == 'White':
                url = reverse('post_tees', kwargs={
                              'name': name, 'tees': 'White'})
                return HttpResponseRedirect(url)
        # Otherwise choose first non white tee
        url = reverse('post_tees', kwargs={
                      'name': name, 'tees': courses[0].tees})
        return HttpResponseRedirect(url)


def post_tees(request, name, tees):
    """Allows the user to post a round or match."""
    # Provide option to switch course
    course_names = get_course_names(name)
    # Get selected course information
    default_course = Course.objects.get(name=name, tees=tees)
    # Check if we need to give options for other tees at this course
    available_courses = Course.objects.filter(name=name)
    available_tees = []
    for i in range(len(available_courses)):
        available_tees.append(available_courses[i].tees)
    index = available_tees.index(f'{tees}')
    # Default to requested tees
    available_tees.insert(0, available_tees.pop(index))
    # Get course information for the given course
    course_info = get_course_info(default_course)
    golfers = User.objects.exclude(pk=1).order_by('first_name')
    # Create default date as a placeholder date
    now = datetime.now()
    date = now.strftime("%Y-%m-%d")
    context = {"course_length": range(1, 10), "course_names": course_names,
               "golfers": golfers, "default_course": default_course,
               "yardages": course_info[2], 'handicaps': course_info[1],
               "pars": course_info[0], "available_tees": available_tees,
               "date": date}
    return render(request, "golf/post.html", context)


def new(request):
    """Allows the user to add a course to the database"""
    if request.method == "POST":
        # Verify and store all course information
        # Verify valid slope
        try:
            slope = int(request.POST['slope'])
        except:
            message = 'Invalid Slope Rating'
            return render(request, "golf/error.html", {'message': message})
        if slope < 55 or slope > 155:
            message = 'Invalid Slope Rating'
            return render(request, "golf/error.html", {'message': message})
        # Verify valid rating
        try:
            rating = float(request.POST['rating'])
        except:
            message = 'Invalid Course Rating'
            return render(request, "golf/error.html", {'message': message})
        # Verify the rating format
        test_rating = str(rating)
        if len(test_rating) != 4:
            message = 'Invalid Course Rating'
            return render(request, "golf/error.html", {'message': message})
        # Check for integers
        for i in range(len(test_rating)):
            if i != 2:
                if not test_rating[i].isdigit():
                    return render(request, "golf/error.html",
                                  {'message': 'Invalid Course Rating'})
            # Check for period
            else:
                if test_rating[i] != '.':
                    return render(request, "golf/error.html",
                                  {'message': 'Invalid Course Rating'})
        if rating < 60 or rating > 81:
            return render(request, "golf/error.html",
                          {'message': 'Invalid Course Rating'})
        # Store yardage information
        yardages = []
        for i in range(1, 19):
            this_yardage = int(request.POST[f"yardages-{i}"])
            if this_yardage < 50 or this_yardage > 999:
                return render(request, "golf/error.html",
                              {'message': 'No hole should have a yardage" \
                              "less than 50 or greater than 999'})
            yardages.append(this_yardage)
        # Verify front nine yardages adds up
        if sum(yardages[0:9]) != int(request.POST['yardages-front']):
            message = "The front nine yardages do" \
                "not add up to the front nine yardage total."
            return render(request, "golf/error.html", {'message': message})
        # Verify back nine yardages add up
        elif sum(yardages[9:]) != int(request.POST['yardages-back']):
            message = "The back nine yardages do" \
                "not add up to the front nine yardage total."
            return render(request, "golf/error.html", {'message': message})
        # Verify total yardages add up
        elif sum(yardages) != int(request.POST['yardages-total']):
            message = "The yardages by hole don't add up to yardage total."
            return render(request, "golf/error.html", {'message': message})
        # Store par information
        pars = []
        for i in range(1, 19):
            this_par = int(request.POST[f"par-{i}"])
            if this_par < 3 or this_par > 5:
                message = "No hole should have a par" \
                    "less than 3 or greater than 5"
                return render(request, "golf/error.html",
                              {'message': message})
            pars.append(this_par)
        # Verify front nine pars add up
        if sum(pars[0:9]) != int(request.POST['par-front']):
            message = "The front nine pars do not" \
                "add up to the front nine par total."
            return render(request, "golf/error.html", {'message': message})
        # Verify back nine pars add up
        elif sum(pars[9:]) != int(request.POST['par-back']):
            message = "The back nine pars do not" \
                "add up to the back nine par total."
            return render(request, "golf/error.html", {'message': message})
        # Verify total pars add up
        elif sum(pars) != int(request.POST['par-total']):
            message = "The pars by hole do not add up to the par total."
            return render(request, "golf/error.html", {'message': message})
        # Store handicap information
        handicaps = []
        for i in range(1, 19):
            this_handicap = int(request.POST[f"handicap-{i}"])
            if this_handicap < 1 or this_handicap > 18:
                message = "No hole should have a handicap" \
                    "rating less than 1 or greater than 18"
                return render(request, "golf/error.html",
                              {'message': message})
            handicaps.append(this_handicap)
        # Check if there are any duplicates
        if len(handicaps) != len(set(handicaps)):
            message = 'Multiple holes cannot have the same handicap.'
            return render(request, "golf/error.html", {'message': message})
        # Check if the user is adding a new course or just a new tee option
        # User is adding a new course
        if request.POST['course-or-tees'] == 'Course':
            # Check if the course name already exists
            all_courses = Course.objects.all()
            for i in range(len(all_courses)):
                if all_courses[i].name == request.POST['new-course-name']:
                    message = 'Course already exists.'
                    return render(request, "golf/error.html",
                                  {'message': message})
            # Create course
            add_course(request, pars, yardages, handicaps)
            return HttpResponseRedirect(reverse('index'))
        # User is just adding a new tee option
        elif request.POST['course-or-tees'] == 'Tees':
            # Check if tee option already exists for the selected course
            all_courses = Course.objects.all()
            for course in all_courses:
                if course.name == request.POST['course-exists'] and \
                        course.tees == request.POST['tees-course-exists']:
                    message = "This tee option already " \
                        "exists for the selected course."
                    return render(request, "golf/error.html",
                                  {'message': message})
            add_course(request, pars, yardages, handicaps, False)  # Add course
            return HttpResponseRedirect(reverse('index'))
        else:
            # Return an error
            message = 'An unexpected error occured. Please try again.'
            return render(request, "golf/error.html", {'message': message})
    else:
        # Display form
        courses = Course.objects.all().order_by('name')
        course_names = []
        for course in courses:
            if course.name not in course_names:
                course_names.append(course.name)
        context = {'course_names': course_names, "course_length": range(1, 10)}
        return render(request, "golf/new.html", context)


def edit(request, match_id):
    """Edits or deletes a match in the database"""
    if request.method == "POST":
        # Add the edited match and delete the unedited match
        # Check if we are deleting or editing match
        if request.POST['action'] == 'Edit Match':
            # Try to post the edited match
            post_success_checker = post_match(request)
            # Successfully posted edited match
            if post_success_checker[0]:
                # Delete the unedited round
                rounds = Round.objects.filter(match=match_id)
                delete_rounds(rounds)
                return HttpResponseRedirect(reverse('index'))
            else:
                # Error
                return render(request, "golf/error.html",
                              {'message': post_success_checker[1]})
        else:
            # Just delete rounds
            rounds = Round.objects.filter(match=match_id)
            delete_rounds(rounds)
            return HttpResponseRedirect(reverse('index'))
    else:
        # Display the scorecard for the given match
        # Retrieve match rounds
        rounds = Round.objects.filter(match=match_id)
        # Provide course names with the given course selected
        course_name = rounds[0].course.name
        course_tees = rounds[0].course.tees
        # Retrieve selected golfers
        golfers = []
        for this_round in rounds:
            golfers.append(this_round.golfer)
        default_course = Course.objects.get(name=course_name,
                                            tees=course_tees)
        # Retrieve scorecard information
        course_info = get_course_info(default_course)
        # Get course date
        date = rounds[0].date
        date = date.strftime("%Y-%m-%d")
        # Get golfer strokes
        golfers_strokes = []
        for golfer_round in rounds:
            golfer_strokes = []
            golfer_scores = Score.objects.filter(round=golfer_round)
            # Store golfer scores
            for score in golfer_scores:
                golfer_strokes.append(score.score)
            golfer_strokes.append(sum(golfer_strokes[9:]))
            golfer_strokes.append(sum(golfer_strokes[:-1]))
            golfer_strokes.insert(9, sum(golfer_strokes[:9]))
            golfer_strokes.insert(0, golfer_round.golfer.first_name)
            golfers_strokes.append(golfer_strokes)
        # Render template
        context = {"course_length": range(1, 10), "course_name": course_name,
                   "golfers": golfers_strokes,
                   "default_course": default_course,
                   "yardages": course_info[2], "handicaps": course_info[1],
                   "pars": course_info[0], "date": date, "match_id": match_id,
                   "tees": course_tees}
        return render(request, "golf/edit.html", context)


def login_view(request):
    """Offer login functionality"""
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
    """Offer logout functionality"""
    logout(request)
    return HttpResponseRedirect(reverse('index'))


def register(request):
    """Offer register functionality"""
    if request.method == "POST":
        # Gather user info
        username = request.POST["username"]
        email = request.POST["email"]
        first_name = request.POST["first-name"]
        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "golf/register.html",
                          {"message": "Passwords must match."})
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
        return HttpResponseRedirect(reverse('index'))  # Homepage redirect
    else:
        return render(request, "golf/register.html")


def page_not_found_view(request, exception):
    """404 Error"""
    return render(request, "golf/error.html", {'message': 'Page Not Found'})


# API Views
@api_view(['GET'])
def api_home(request):
    # Gather statistics for golfers who have played rounds
    all_golfers = User.objects.filter(has_rounds=True)
    all_stats = []
    for golfer in all_golfers:
        # Exclude solo rounds
        golfers_rounds = Round.objects.filter(
            golfer=golfer, date__year=2023).exclude(solo_round=True)
        if len(golfers_rounds) > 0:
            stats = get_stats(golfers_rounds)
            golfer_info = {}
            golfer_info['Golfer'] = stats[0]
            golfer_info['Rounds'] = stats[1]
            golfer_info['Avg Score'] = stats[2]
            golfer_info['Avg Par'] = stats[3]
            golfer_info['Best Score'] = stats[4]
            golfer_info['Birdies Per'] = stats[5]
            golfer_info['Pars Per'] = stats[6]
            golfer_info['Bogeys Per'] = stats[7]
            golfer_info['Doubles Per'] = stats[8]
            golfer_info['Triples Per'] = stats[9]
            golfer_info['Maxes Per'] = stats[10]
            golfer_info['Par 3 Avg'] = stats[11]
            golfer_info['Par 4 Avg'] = stats[12]
            golfer_info['Par 5 Avg'] = stats[13]
            golfer_info['Eagles'] = stats[14]
            all_stats.append(golfer_info)
    bart_birdies = get_bart_birdies()
    context = {'all_stats': all_stats, 'bart_birdies': bart_birdies}
    return Response(context)


@api_view(['GET'])
def getData(request):
    person = {'name': 'Dennis', 'age': 28}
    return Response(person)


@api_view(['GET'])
def api_golfer(request, golfer):
    # Get golfers statistics
    this_golfer = User.objects.get(first_name=golfer)
    golfer_rounds = Round.objects.filter(
        golfer=this_golfer, date__year=2023).order_by('-date')
    if len(golfer_rounds) > 0:
        stats = get_stats(golfer_rounds)
    else:
        error_message = "The selected golfer has not played a round yet in this year"
        return Response({'message': 'fail', 'error': True, 'code': 500, 'result': {'Message': error_message}})
    # Only offer the option to switch to golfers that have played a round
    all_golfers = User.objects.filter(has_rounds=True).order_by('first_name')
    # Gather a scorecard for every round the golfer has played
    scorecards = []
    for this_round in golfer_rounds:
        scorecard = get_scorecard(this_round)
        scorecards.append(scorecard)
    golfers = []
    for golfer in all_golfers:
        golfers.append(golfer.first_name)
    golfer_info = {}
    for stat in stats:
        golfer_info['Golfer'] = stats[0]
        golfer_info['Rounds'] = stats[1]
        golfer_info['Avg Score'] = stats[2]
        golfer_info['Avg Par'] = stats[3]
        golfer_info['Best Score'] = stats[4]
        golfer_info['Birdies Per'] = stats[5]
        golfer_info['Pars Per'] = stats[6]
        golfer_info['Bogeys Per'] = stats[7]
        golfer_info['Doubles Per'] = stats[8]
        golfer_info['Triples Per'] = stats[9]
        golfer_info['Maxes Per'] = stats[10]
        golfer_info['Par 3 Avg'] = stats[11]
        golfer_info['Par 4 Avg'] = stats[12]
        golfer_info['Par 5 Avg'] = stats[13]
        golfer_info['Eagles'] = stats[14]
    golfer_info_array = [golfer_info]
    # Gather a scorecard for every round the golfer has played
    scorecards = []
    for this_round in golfer_rounds:
        scorecard = get_scorecard(this_round)
        scorecards.append(scorecard)
    api_scorecards = []
    for scorecard in scorecards:
        api_scorecard = {}
        api_scorecard['course_name'] = scorecard['course'].name
        api_scorecard['tees'] = scorecard['course'].tees
        api_scorecard['date'] = scorecard['round'].date
        api_scorecard['yardages'] = scorecard['yardages']
        api_scorecard['handicaps'] = scorecard['handicaps']
        api_scorecard['strokes'] = scorecard['strokes']
        api_scorecard['to_pars'] = scorecard['to_pars']
        api_scorecard['pars'] = scorecard['pars']
        api_scorecard['match'] = scorecard['match_id']
        api_scorecards.append(api_scorecard)

    context = {'stats': golfer_info_array,
               'all_golfers': golfers, 'scorecards': api_scorecards}
    return Response(context)


@api_view(['GET'])
def get_course_data(request, course, tees):
    try:
        course = Course.objects.get(name=course, tees=tees)
    except ObjectDoesNotExist:
        tee_options = get_tee_options(course, tees)
        return Response({'message': 'fail', 'error': True, 'code': 500, 'tee': tee_options})
    else:
        courses = Course.objects.all().order_by('name')
        course_data = get_course_info(course)
        tee_options = get_tee_options(course, tees)
        unique_course_names = []
        for course in courses:
            if course.name not in unique_course_names:
                unique_course_names.append(course.name)
        all_golfers = User.objects.filter(
            has_rounds=True).order_by('first_name')
        golfer_names = []
        for golfer in all_golfers:
            golfer_names.append(golfer.first_name)
        context = {'course_data': course_data, 'tee_options': tee_options,
                   'course_names': unique_course_names, 'golfer_names': golfer_names}
        return Response(context)


@api_view(['GET'])
def api_get_all_course_data(request, course_name):
    try:
        courses = Course.objects.filter(name=course_name)
    except:
        return Response({'message': 'fail', 'error': True, 'code': 500, })
    course_data = []
    tee_options = []
    for course in courses:
        tee_options.append(course.tees)
        this_course_info = {}
        this_course_info['tee'] = course.tees
        this_course_info['slope'] = course.slope
        this_course_info['course-rating'] = course.course_rating
        this_course_info['hole-information'] = get_course_info(course)
        course_data.append(this_course_info)
    context = {'course_data': course_data, 'tee_options': tee_options}
    return Response(context)


@api_view(['PUT'])
def api_edit_course(request, course_name, tee):
    try:
        course = Course.objects.get(name=course_name, tees=tee)
    except:
        return Response({'message': 'fail', 'error': True, 'code': 500, })
    # Parse request data
    slope = request.data['slope']
    course_rating = request.data['courseRating']
    yardages = request.data['yardages']
    handicaps = request.data['handicaps']
    pars = request.data['pars']
    # Verify and store all course information
    # Verify valid slope
    try:
        slope = int(slope)
    except:
        message = 'Invalid Slope Rating'
        return Response({'message': 'fail', 'error': True, 'code': 500, 'result': {'Message': message}})
    if slope < 55 or slope > 155:
        message = 'Invalid Slope Rating'
        return Response({'message': 'fail', 'error': True, 'code': 500, 'result': {'Message': message}})
    # Verify valid course rating
    try:
        course_rating = float(course_rating)
    except:
        message = 'Invalid course rating.'
        return Response({'message': 'fail', 'error': True, 'code': 500, 'result': {'Message': message}})
    # Verify the rating format
    test_rating = str(course_rating)
    if len(test_rating) != 4:
        message = 'Invalid Course Rating'
        return Response({'message': 'fail', 'error': True, 'code': 500, 'result': {'Message': message}})
    # Check for integers
    for i in range(len(test_rating)):
        if i != 2:
            if not test_rating[i].isdigit():
                message = 'Invalid Course Rating'
                return Response({'message': 'fail', 'error': True, 'code': 500, 'result': {'Message': message}})
        # Check for period
        else:
            if test_rating[i] != '.':
                message = 'Invalid Course Rating'
                return Response({'message': 'fail', 'error': True, 'code': 500, 'result': {'Message': message}})
    if course_rating < 60 or course_rating > 81:
        message = 'Invalid Course Rating'
        return Response({'message': 'fail', 'error': True, 'code': 500, 'result': {'Message': message}})
    # Verify Selected Tees
    tee_options = ['White', 'Blue', 'Red']
    if tee not in tee_options:
        message = 'Invalid Tee Selected'
        return Response({'message': 'fail', 'error': True, 'code': 500, 'result': {'Message': message}})
    # Store yardage information
    for yardage in yardages:
        try:
            this_yardage = int(yardage)
        except:
            message = 'Invalid Yardages'
            return Response({'message': 'fail', 'error': True, 'code': 500, 'result': {'Message': message}})
        if this_yardage < 50 or this_yardage > 999:
            message = 'Invalid Yardages'
            return Response({'message': 'fail', 'error': True, 'code': 500, 'result': {'Message': message}})
    # Store par information
    for par in pars:
        try:
            this_par = int(par)
        except:
            message = 'Invalid Pars'
            return Response({'message': 'fail', 'error': True, 'code': 500, 'result': {'Message': message}})
        if this_par < 3 or this_par > 5:
            message = 'Invalid Pars'
            return Response({'message': 'fail', 'error': True, 'code': 500, 'result': {'Message': message}})
    # Store handicap information
    for handicap in handicaps:
        try:
            this_handicap = int(handicap)
        except:
            message = 'Invalid Handicaps'
            return Response({'message': 'fail', 'error': True, 'code': 500, 'result': {'Message': message}})
        if this_handicap < 1 or this_handicap > 18:
            message = 'Invalid Handicaps'
            return Response({'message': 'fail', 'error': True, 'code': 500, 'result': {'Message': message}})
    # Check if there are any duplicates
    if len(handicaps) != len(set(handicaps)):
        message = 'Multiple holes cannot have the same handicap.'
        return Response({'message': 'fail', 'error': True, 'code': 500, 'result': {'Message': message}})
    # Update data
    yardages_front = int(sum(yardages[:9]))
    yardages_back = int(sum(yardages[9:]))
    yaradage_total = int(sum(yardages))
    pars_front = int(sum(pars[:9]))
    pars_back = int(sum(pars[9:]))
    pars_total = int(sum(pars))
    course.course_rating = float(course_rating)
    course.slope = slope
    course.front_par = pars_front
    course.back_par = pars_back
    course.par = pars_total
    course.front_yardage = yardages_front
    course.back_yardage = yardages_back
    course.yardage = yaradage_total
    course.save()
    holes = Hole.objects.filter(course=course).order_by('tee')
    for i in range(len(holes)):
        holes[i].par = pars[i]
        holes[i].yardage = yardages[i]
        holes[i].handicap = handicaps[i]
        holes[i].save()
    return Response({'message': 'success', 'error': False})


@api_view(['GET'])
def api_course(request, course, tees, golfer):
    """Shows a golfers statistics, hole averages, and rounds on a course"""
    # Provide option to switch golfer and/or course
    all_golfers = User.objects.filter(has_rounds=True).order_by('first_name')
    course_names = get_course_names(course)
    tee_options = get_tee_options(course, tees)
    if tees not in tee_options:
        message = "This course is not in our database."
        return Response({'message': 'fail', 'error': True, 'code': 500, 'result': {'Message': message}, 'tees': tee_options})
    # Retrieve rounds that this golfer has played at this course
    course = Course.objects.get(name=course, tees=tees)
    golfer = User.objects.get(first_name=golfer)
    # Include solo rounds
    rounds = Round.objects.filter(golfer=golfer,
                                  course=course,
                                  date__year=2023).order_by('-date')
    # Ensure the golfer has played a round at this course
    if len(rounds) == 0:
        message = 'The selected golfer has not played the selected course'
        return Response({'message': 'fail', 'error': True, 'code': 500, 'result': {'Message': message}, 'tees': tee_options})
    # Retrieve a scorecard for every round
    scorecards = []
    for round in rounds:
        scorecard = get_scorecard(round)
        scorecards.append(scorecard)
    stats = get_stats(rounds)  # Retrieve stats for this golfer at this course
    # Retrieve golfers hole averages at this course
    avg_scorecard = get_course_avg_scorecard(rounds)
    avg_scorecard = api_avg_scorecard(avg_scorecard)
    stats = api_stats(stats)
    scorecards = api_scorecards(scorecards)
    golfers = []
    for golfer in all_golfers:
        golfers.append(golfer.first_name)
    context = {'stats': [stats], 'avg_scorecard': avg_scorecard,
               'scorecards': scorecards, 'courses': course_names,
               'tees': tee_options, 'golfer': golfer.first_name,
               'all_golfers': golfers}
    return Response(context)


def api_avg_scorecard(scorecard):
    api_scorecard = {}
    api_scorecard['course_name'] = scorecard['course'].name
    api_scorecard['tees'] = scorecard['course'].tees
    api_scorecard['yardages'] = scorecard['yardages']
    api_scorecard['handicaps'] = scorecard['handicaps']
    api_scorecard['strokes'] = scorecard['strokes']
    api_scorecard['to_pars'] = scorecard['to_pars']
    api_scorecard['pars'] = scorecard['pars']
    try:
        api_scorecard['match'] = scorecard['match_id']
    except:
        pass
    return api_scorecard


@api_view(['GET'])
def api_vs(request, golfer1, golfer2):
    """Returns an object for vs API request"""
    if golfer1 == golfer2:
        error_message = "You must select two different golfers."
        return Response({'message': 'fail', 'error': True, 'code': 500, 'result': {'Message': error_message}})
     # Offer option to switch to any golfer
    all_golfers = User.objects.filter(has_rounds=True).order_by('first_name')
    # Retrieve all rounds for selected golfers
    golfer_one = User.objects.get(first_name=golfer1)
    golfer_two = User.objects.get(first_name=golfer2)
    golfer_one_rounds = Round.objects.filter(
        golfer=golfer_one, date__year=2023)
    golfer_two_rounds = Round.objects.filter(
        golfer=golfer_two, date__year=2023)
    # Check both golfers have played a round
    if len(golfer_one_rounds) == 0 or len(golfer_two_rounds) == 0:
        message = "The selected golfers have not played each other."
        return Response({'message': 'fail', 'error': True, 'code': 500, 'result': {'Message': message}})
    # Check which rounds are on the same scorecard / are a match
    golfer_one_match_ids = []
    golfer_two_match_ids = []
    # All golfer one matches
    for this_round in golfer_one_rounds:
        if this_round.match not in golfer_one_match_ids:
            golfer_one_match_ids.append(this_round.match)
    # All golfer two matches
    for this_round in golfer_two_rounds:
        if this_round.match not in golfer_two_match_ids:
            golfer_two_match_ids.append(this_round.match)
    # Find common matches
    cumulative_match_ids = []
    for id in golfer_one_match_ids:
        if id in golfer_two_match_ids:
            cumulative_match_ids.append(id)
    if len(cumulative_match_ids) == 0:
        error_message = "The selected golfers have not played each other."
        return Response({'message': 'fail', 'error': True, 'code': 500, 'result': {'Message': error_message}})
    # Retrieve golfer rounds that are a match between the two golfers
    golfer_one_rounds = \
        Round.objects.filter(golfer=golfer_one, date__year=2023,
                             match__in=cumulative_match_ids).order_by('-date')
    golfer_two_rounds = \
        Round.objects.filter(golfer=golfer_two, date__year=2023,
                             match__in=cumulative_match_ids).order_by('-date')
    # Get stats for both golfers
    golfer_one_stats = get_stats(golfer_one_rounds)
    golfer_two_stats = get_stats(golfer_two_rounds)
    # Get scorecards for each match
    both_golfers_rounds = [golfer_one_rounds, golfer_two_rounds]
    scorecards = get_vs_scorecards(both_golfers_rounds)
    # Calculate the records between the two golfers
    match_checker = {'golfer_one_wins': 0, 'golfer_two_wins': 0, 'ties': 0}
    for scorecard in scorecards:
        # Golfer one won this match
        if scorecard['strokes_one'][-1] < scorecard['strokes_two'][-1]:
            match_checker['golfer_one_wins'] += 1
        # Golfer two won this match
        elif scorecard['strokes_one'][-1] > scorecard['strokes_two'][-1]:
            match_checker['golfer_two_wins'] += 1
        # This match was a tie
        else:
            match_checker['ties'] += 1
    # Record wins and ties
    golfer_one_wins = match_checker['golfer_one_wins']
    golfer_two_wins = match_checker['golfer_two_wins']
    ties = match_checker['ties']
    # Message for golfer one winning or tie
    if golfer_one_wins >= golfer_two_wins:
        winner = f"{golfer_one} is {golfer_one_wins}"
        loser = f"-{golfer_two_wins}-{ties} vs {golfer_two}"
        record = winner + loser
    # Message for golfer two winning
    else:
        winner = f"{golfer_two} is {golfer_two_wins}"
        loser = f"-{golfer_one_wins}-{ties} vs {golfer_one}"
        record = winner + loser
    # Sort stats by which golfer has best average round
    if golfer_one_stats[2] > golfer_two_stats[2]:
        buffer = golfer_one_stats
        golfer_one_stats = golfer_two_stats
        golfer_two_stats = buffer
    golfers = []
    for golfer in all_golfers:
        golfers.append(golfer.first_name)
    golfer_one_stats = api_stats(golfer_one_stats)
    golfer_two_stats = api_stats(golfer_two_stats)
    scorecards = api_scorecards(scorecards, True)
    context = {'stats_one': golfer_one_stats, 'stats_two': golfer_two_stats,
               'scorecards': scorecards,
               'all_golfers': golfers,
               'record': record}
    return Response(context)


@api_view(['POST'])
def api_post(request):
    """Post a round to the database"""
    data = request.data
    golfer_count = data['golferCount']
    empty_golfers = data['golfers']
    golfers = [golfer for golfer in empty_golfers if golfer != '']
    date = data['date']
    date = datetime.fromisoformat(date[:-1])
    date = date.strftime('%Y-%m-%d')
    course = data['course']
    tee = data['tee']
    golfer_scores = data['strokes']
    acceptable_scores = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    if len(golfers) != len(set(golfers)) or len(golfers) != golfer_count:
        error_message = "Each golfer should be unique."
        return Response({'message': 'fail', 'error': True, 'code': 500, 'result': {'Message': error_message}})
    if golfer_count < 1 or golfer_count > 4:
        error_message = "Each golfer should be unique."
        return Response({'message': 'fail', 'error': True, 'code': 500, 'result': {'Message': error_message}})
    for i in range(golfer_count):
        for j in range(18):
            if golfer_scores[i][j] not in acceptable_scores:
                error_message = "All scores entered should be single numbers."
                return Response({'message': 'fail', 'error': True, 'code': 500, 'result': {'Message': error_message}})
    # Store round information
    # Create new match_id
    highest_matches =  \
        Round.objects.all().order_by('-match').values()
    highest_match = highest_matches[0]['match']
    match = highest_match + 1
    solo_round = golfer_count == 1
    # Save a round for each golfer
    for i in range(golfer_count):
        golfer_name = golfers[i]
        golfer = User.objects.get(first_name=golfer_name)
        course = Course.objects.get(
            name=course, tees=tee)
        this_round = Round(golfer=golfer, course=course,
                           date=date, match=match, solo_round=solo_round)
        this_round.save()
        # Add golfer to those who have rounds played
        golfer.has_rounds = True
        golfer.save()
        for j in range(0, 18):
            score = golfer_scores[i][j]
            hole = Hole.objects.get(course=course, tee=j+1)
            this_score = Score(
                score=score, golfer=golfer, round=this_round, hole=hole)
            this_score.save()
    return Response({'message': 'success', 'error': False,  'result': {'Message': "Added Round Successfully"}})


@api_view(['GET', 'POST'])
def api_new(request):
    """Allows the user to add a course to the database"""
    if request.method == "GET":
        # Display form
        courses = Course.objects.all().order_by('name')
        course_names = []
        for course in courses:
            if course.name not in course_names:
                course_names.append(course.name)
        context = {'course_names': course_names}
        return Response(context)
    elif request.method == "POST":
        # Parse request data
        course = request.data['course']
        tee = request.data['tee']
        slope = request.data['slope']
        course_rating = request.data['courseRating']
        yardages = request.data['yardages']
        handicaps = request.data['handicaps']
        pars = request.data['pars']
        submit_option = request.data['submitOption']
        new_course_name = request.data['newCourseName']
        capitalized_words = [word.capitalize()
                             for word in new_course_name.split()]
        new_course_name = ' '.join(capitalized_words)

        # Verify and store all course information
        # Verify valid slope
        try:
            slope = int(slope)
        except:
            message = 'Invalid Slope Rating'
            return Response({'message': 'fail', 'error': True, 'code': 500, 'result': {'Message': message}})
        if slope < 55 or slope > 155:
            message = 'Invalid Slope Rating'
            return Response({'message': 'fail', 'error': True, 'code': 500, 'result': {'Message': message}})
        # Verify valid course rating
        try:
            course_rating = float(course_rating)
        except:
            message = 'Invalid course rating.'
            return Response({'message': 'fail', 'error': True, 'code': 500, 'result': {'Message': message}})
        # Verify the rating format
        test_rating = str(course_rating)
        if len(test_rating) != 4:
            message = 'Invalid Course Rating'
            return Response({'message': 'fail', 'error': True, 'code': 500, 'result': {'Message': message}})
        # Check for integers
        for i in range(len(test_rating)):
            if i != 2:
                if not test_rating[i].isdigit():
                    message = 'Invalid Course Rating'
                    return Response({'message': 'fail', 'error': True, 'code': 500, 'result': {'Message': message}})
            # Check for period
            else:
                if test_rating[i] != '.':
                    message = 'Invalid Course Rating'
                    return Response({'message': 'fail', 'error': True, 'code': 500, 'result': {'Message': message}})
        if course_rating < 60 or course_rating > 81:
            message = 'Invalid Course Rating'
            return Response({'message': 'fail', 'error': True, 'code': 500, 'result': {'Message': message}})
        # Verify Selected Tees
        tee_options = ['White', 'Blue', 'Red']
        if tee not in tee_options:
            message = 'Invalid Tee Selected'
            return Response({'message': 'fail', 'error': True, 'code': 500, 'result': {'Message': message}})
        # Store yardage information
        for yardage in yardages:
            try:
                this_yardage = int(yardage)
            except:
                message = 'Invalid Yardages'
                return Response({'message': 'fail', 'error': True, 'code': 500, 'result': {'Message': message}})
            if this_yardage < 50 or this_yardage > 999:
                message = 'Invalid Yardages'
                return Response({'message': 'fail', 'error': True, 'code': 500, 'result': {'Message': message}})
        # Store par information
        for par in pars:
            try:
                this_par = int(par)
            except:
                message = 'Invalid Pars'
                return Response({'message': 'fail', 'error': True, 'code': 500, 'result': {'Message': message}})
            if this_par < 3 or this_par > 5:
                message = 'Invalid Pars'
                return Response({'message': 'fail', 'error': True, 'code': 500, 'result': {'Message': message}})
        # Store handicap information
        for handicap in handicaps:
            try:
                this_handicap = int(handicap)
            except:
                message = 'Invalid Handicaps'
                return Response({'message': 'fail', 'error': True, 'code': 500, 'result': {'Message': message}})
            if this_handicap < 1 or this_handicap > 18:
                message = 'Invalid Handicaps'
                return Response({'message': 'fail', 'error': True, 'code': 500, 'result': {'Message': message}})
        # Check if there are any duplicates
        if len(handicaps) != len(set(handicaps)):
            message = 'Multiple holes cannot have the same handicap.'
            return Response({'message': 'fail', 'error': True, 'code': 500, 'result': {'Message': message}})
        # Check if the user is adding a new course or just a new tee option
        # User is adding a new course
        if submit_option == 'course':
            # Check if the course name already exists
            all_courses = Course.objects.all()
            for i in range(len(all_courses)):
                if all_courses[i].name == new_course_name:
                    message = 'Course Name Already Exists'
                    return Response({'message': 'fail', 'error': True, 'code': 500, 'result': {'Message': message}})
            # Create course
            api_add_course(request, pars, yardages, handicaps)
            message = 'Course Submitted'
            return Response({'message': 'success', 'error': False, 'result': {'Message': message}})
        # User is just adding a new tee option
        elif submit_option == 'tees':
            # Check if tee option already exists for the selected course
            all_courses = Course.objects.all()
            for this_course in all_courses:
                if this_course.name == course and this_course.tees == tee:
                    message = "This tee option already " \
                        "exists for the selected course."
                    return Response({'message': 'fail', 'error': True, 'code': 400, 'result': {'Message': message}}, status=status.HTTP_400_BAD_REQUEST)
            api_add_course(request, pars, yardages,
                           handicaps, False)  # Add course
            message = 'Course Submitted'
            return Response({'message': 'success', 'error': False, 'result': {'Message': message}})
    else:
        return Response({'message': 'fail', 'error': True, 'code': 500, 'result': {'Message': "Can only submit a POST or GET request."}})


@api_view(['GET', 'POST'])
def api_edit(request, match_id):
    """Edits or deletes a match in the database via API"""
    if request.method == 'GET':
        # Retrieve match rounds
        rounds = Round.objects.filter(match=match_id)
        # Provide course names with the given course selected
        course_name = rounds[0].course.name
        course_tees = rounds[0].course.tees
        tee_options = get_tee_options(course_name, course_tees)
        # Retrieve selected golfers
        golfers = []
        for this_round in rounds:
            golfers.append(this_round.golfer)
        default_course = Course.objects.get(name=course_name,
                                            tees=course_tees)
        golfers_names = []
        for golfer in golfers:
            golfers_names.append(golfer. first_name)
        # Retrieve scorecard information
        course_info = get_course_info(default_course)
        # Get course date
        date = rounds[0].date
        date = date.strftime("%Y-%m-%d")
        # Provide golfer options
        all_golfers = User.objects.filter(
            has_rounds=True).order_by('first_name')
        golfer_options = []
        for golfer in all_golfers:
            if golfer.first_name not in golfer_options:
                golfer_options.append(golfer.first_name)
        # Provide course options
        courses = Course.objects.all().order_by('name')
        course_names = []
        for course in courses:
            if course.name not in course_names:
                course_names.append(course.name)
        # Get golfer strokes
        golfers_strokes = []
        for golfer_round in rounds:
            golfer_strokes = []
            golfer_scores = Score.objects.filter(round=golfer_round)
            # Store golfer scores
            for score in golfer_scores:
                golfer_strokes.append(score.score)
            golfers_strokes.append(golfer_strokes)
        context = {"course_name": course_name,
                   "course_names": course_names,
                   "golfers": golfers_names,
                   "golfer_options": golfer_options,
                   "golfers_strokes": golfers_strokes,
                   "yardages": course_info[2], "handicaps": course_info[1],
                   "pars": course_info[0], "date": date, "match_id": match_id,
                   "course_tees": course_tees, "tee_options": tee_options}
        return Response(context)
    elif request.method == 'POST':
        # Add the edited match and delete the unedited match
        # Check if we are deleting or editing match
        try:
            # If there is a match ID we are editing
            match_id = request.data['matchId']
        # Delete match
        except:
            rounds = Round.objects.filter(match=match_id)
            delete_rounds(rounds)
            context = {"Round Deleted": "Success"}
            return Response(context)
        data = request.data
        golfer_count = data['golferCount']
        golfers = data['golfers']
        date = data['date']
        date = datetime.fromisoformat(date[:-1])
        date = date.strftime('%Y-%m-%d')
        course = data['course']
        tee = data['tee']
        golfer_scores = data['strokes']
        acceptable_scores = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        if len(golfers) != len(set(golfers)) or '' in golfers:
            return Response({'message': 'fail', 'error': True, 'code': 500, 'result': {'Message': "Each golfer should be unique"}})
        if golfer_count < 1 or golfer_count > 4:
            return Response({'message': 'fail', 'error': True, 'code': 500, 'result': {'Message': "There was an error processing your request."}})
        for i in range(golfer_count):
            for j in range(18):
                if golfer_scores[i][j] not in acceptable_scores:
                    return Response({'message': 'fail', 'error': True, 'code': 500, 'result': {'Message': "All scores entered should be single numbers."}})
        # Store round information
        # Create new match_id
        highest_matches =  \
            Round.objects.all().order_by('-match').values()
        highest_match = highest_matches[0]['match']
        match = highest_match + 1
        # Save a round for each golfer
        for i in range(golfer_count):
            golfer_name = golfers[i]
            golfer = User.objects.get(first_name=golfer_name)
            course = Course.objects.get(
                name=course, tees=tee)
            this_round = Round(golfer=golfer, course=course,
                               date=date, match=match)
            this_round.save()
            # Add golfer to those who have rounds played
            golfer.has_rounds = True
            golfer.save()
            # Store each score
            for j in range(0, 18):
                score = golfer_scores[i][j]
                hole = Hole.objects.get(course=course, tee=j+1)
                this_score = Score(
                    score=score, golfer=golfer, round=this_round, hole=hole)
                this_score.save()
        # Delete the unedited rounds
        rounds = Round.objects.filter(match=match_id)
        delete_rounds(rounds)
        return Response({'message': 'success', 'error': False,  'result': {'Message': "Edited Round Successfully"}})
    else:
        return Response({'message': 'Denied access', 'error': True})
