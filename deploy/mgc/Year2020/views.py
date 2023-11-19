from django.db import IntegrityError
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse
from django.core.paginator import Paginator
from golf.models import User, Course, Score, Round
from golf.helpers import get_stats, get_scorecard, \
    get_course_avg_scorecard, get_vs_scorecards, \
    get_course_names, get_tee_options


def index(request):
    """Show statistics for all golfers, excluding solo rounds"""
    # Gather statistics for golfers who have played rounds
    all_golfers = User.objects.filter(has_rounds=True)
    all_stats = []
    for golfer in all_golfers:
        # Exclude solo rounds
        golfers_rounds = Round.objects.filter(golfer=golfer,
                                              date__year=2020).exclude(
            match=0)
        if len(golfers_rounds) > 0:
            stats = get_stats(golfers_rounds)
            all_stats.append(stats)
    # Sort stats by average score

    def avg_score(golfers_stats):
        return golfers_stats[2]
    all_stats.sort(key=avg_score)
    # Render template
    context = {'all_stats': all_stats}
    return render(request, "2020/index.html", context)


def golfer(request, golfer):
    """Shows a golfers rounds and statistics, including solo rounds"""
    # Get golfers statistics
    this_golfer = User.objects.get(first_name=golfer)
    golfer_rounds = Round.objects.filter(
        golfer=this_golfer, date__year=2020).order_by('-date')
    if len(golfer_rounds) > 0:
        stats = get_stats(golfer_rounds)
    # Offer the option to switch to those that have played a round in 2020
    all_golfers = User.objects.all()
    golfers_2020 = []
    for golfer in all_golfers:
        golfers_rounds = Round.objects.filter(golfer=golfer, date__year=2020)
        if len(golfers_rounds) > 0:
            golfers_2020.append(golfer)
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
               'all_golfers': golfers_2020}
    return render(request, "2020/golfer.html", context)


def course(request, course, tees, golfer):
    """Shows a golfers statistics, hole averages, and rounds on a course"""
    # Provide option to switch golfer and/or course
    all_golfers = User.objects.filter(has_rounds=True)
    course_names = get_course_names(course)
    tee_options = get_tee_options(course, tees)
    # Retrieve rounds that this golfer has played at this course
    course = Course.objects.get(name=course, tees=tees)
    golfer = User.objects.get(first_name=golfer)
    # Include solo rounds
    rounds = Round.objects.filter(golfer=golfer,
                                  course=course,
                                  date__year=2020).order_by('-date')
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
    # Paginate scorecards
    scorecards = Paginator(scorecards, 3)
    page_number = request.GET.get('page')
    this_page_scorecard = scorecards.get_page(page_number)
    # Render template
    context = {'stats': stats, 'avg_scorecard': avg_scorecard,
               'scorecards': this_page_scorecard, 'courses': course_names,
               'tees': tee_options, 'golfer': golfer,
               'course_length': range(1, 10), 'all_golfers': all_golfers}
    return render(request, "2020/course.html", context)


def vs(request, golfer1, golfer2):
    """Shows stats of one golfer vs another"""
    # Ensure two distinct golfers were selected
    if golfer1 == golfer2:
        message = "Must select two separate golfers."
        return render(request, "golf/error.html", {'message': message})
    # Offer option to switch to any golfer
    all_golfers = User.objects.filter(has_rounds=True)
    # Retrieve all rounds for selected golfers
    golfer_one = User.objects.get(first_name=golfer1)
    golfer_two = User.objects.get(first_name=golfer2)
    golfer_one_rounds = Round.objects.filter(golfer=golfer_one,
                                             date__year=2020)
    golfer_two_rounds = Round.objects.filter(golfer=golfer_two,
                                             date__year=2020)
    # Check both golfers have playes a round in 2020
    if len(golfer_one_rounds) == 0 or len(golfer_two_rounds) == 0:
        message = 'At least one golfer has not played a round this year.'
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
        Round.objects.filter(golfer=golfer_one, date__year=2020,
                             match__in=cumulative_match_ids).order_by('-date')
    golfer_two_rounds = \
        Round.objects.filter(golfer=golfer_two, date__year=2020,
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
    return render(request, "2020/vs.html", context)


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
