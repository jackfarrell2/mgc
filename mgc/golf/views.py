from datetime import datetime
import this
from django.db import IntegrityError
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse
from django.core.paginator import Paginator
from .models import User, Course, Hole, Score, Round
from golf.helpers import get_stats, get_scorecard, \
    get_course_avg_scorecard, get_vs_scorecards, add_course


def index(request):
    """Show statistics for all golfers, excluding solo rounds"""
    # Only show statistics for golfers who have played rounds
    all_golfers = []
    all_rounds = Round.objects.all()
    for round in all_rounds:
        if round.golfer not in all_golfers:
            all_golfers.append(round.golfer)
    # Gather statistics for all golfers
    all_stats = []
    for golfer in all_golfers:
        # Exclude solo rounds
        golfers_rounds = Round.objects.filter(golfer=golfer).exclude(match=0)
        stats = get_stats(golfers_rounds)
        all_stats.append(stats)

    # Sort stats by average score
    def avg_score(golfers_stats):
        return golfers_stats[2]
    all_stats.sort(key=avg_score)
    context = {'all_stats': all_stats}
    return render(request, "golf/index.html", context)


def golfer(request, golfer):
    """Shows a golfers rounds and statistics, including solo rounds"""
    # Get golfers statistics
    this_golfer = User.objects.get(first_name=golfer)
    golfer_rounds = Round.objects.filter(golfer=this_golfer).order_by('-date')
    stats = get_stats(golfer_rounds)
    # Only offer the option to switch to golfers that have played a round
    all_golfers = []
    all_rounds = Round.objects.all()
    for round in all_rounds:
        if round.golfer not in all_golfers:
            all_golfers.append(round.golfer)
    # Gather a scorecard for every round the golfer has played
    scorecards = []
    for this_round in golfer_rounds:
        scorecard = get_scorecard(this_round)
        scorecards.append(scorecard)
    # Paginate scorecards
    scorecards = Paginator(scorecards, 3)
    page_number = request.GET.get('page')
    this_page_scorecard = scorecards.get_page(page_number)
    context = {'stats': stats, 'scorecards': this_page_scorecard,
               'golfer': this_golfer, 'course_length': range(1, 10),
               'all_golfers': all_golfers}
    return render(request, "golf/golfer.html", context)


def course(request, course, tees, golfer):
    """Shows a golfers statistics, hole averages, and rounds on a course"""
    # Provide option to switch golfer and/or course
    all_golfers = User.objects.all()
    courses = Course.objects.all()
    # Filter out duplicate course names
    course_names = []
    for each_course in courses:
        if each_course.name not in course_names:
            course_names.append(each_course.name)
    # Move the selected course to the front of the drop down menu
    selected_course_index = course_names.index(course)
    if selected_course_index != 0:
        course_names.insert(0, course_names.pop(selected_course_index))
    # Offer tee options for each available tee at this given course
    tee_options = []
    duplicate_courses = Course.objects.filter(name=course)
    for course in duplicate_courses:
        tee_options.append(course.tees)
    # Move the selected tee to the front of the drop down menu
    selected_tee_index = tee_options.index(tees)
    if selected_tee_index != 0:
        tee_options.insert(0, tee_options.pop(selected_tee_index))
    # Retrieve rounds that this golfer has played at this course
    course = Course.objects.get(name=course, tees=tees)
    golfer = User.objects.get(first_name=golfer)
    # Include solo rounds
    rounds = Round.objects.filter(golfer=golfer,
                                  course=course).order_by('-date')
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
    context = {'stats': stats, 'avg_scorecard': avg_scorecard,
               'scorecards': this_page_scorecard, 'courses': course_names,
               'tees': tee_options, 'golfer': golfer,
               'course_length': range(1, 10), 'all_golfers': all_golfers}
    return render(request, "golf/course.html", context)


def vs(request, golfer1, golfer2):
    """Shows stats of one golfer vs another"""
    # Ensure two golfers were selected
    if golfer1 == golfer2:
        message = "Must select two separate golfers."
        return render(request, "golf/error.html", {'message': message})
    all_golfers = User.objects.all()  # Offer option to switch to any golfer
    # Retrieve all rounds for selected golfers
    golfer_one = User.objects.get(first_name=golfer1)
    golfer_two = User.objects.get(first_name=golfer2)
    golfer_one_rounds = Round.objects.filter(golfer=golfer_one)
    golfer_two_rounds = Round.objects.filter(golfer=golfer_two)
    golfer_one_match_ids = []
    golfer_two_match_ids = []
    # Check which rounds are on the same scorecard / are a match
    for this_round in golfer_one_rounds:
        if this_round.match not in golfer_one_match_ids:
            golfer_one_match_ids.append(this_round.match)
    for this_round in golfer_two_rounds:
        if this_round.match not in golfer_two_match_ids:
            golfer_two_match_ids.append(this_round.match)
    cumulative_match_ids = []
    for id in golfer_one_match_ids:
        if id in golfer_two_match_ids:
            cumulative_match_ids.append(id)
    # Retrieve golfer rounds that are a match between the two golfers
    golfer_one_rounds = \
        Round.objects.filter(golfer=golfer_one,
                             match__in=cumulative_match_ids).order_by('-date')
    golfer_two_rounds = \
        Round.objects.filter(golfer=golfer_two,
                             match__in=cumulative_match_ids).order_by('-date')
    # Check if the golfers have played against one another
    if len(golfer_one_rounds) == 0:
        message = 'The selected golfers have not played each other.'
        return render(request, "golf/error.html", {'message': message})
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
    context = {'stats_one': golfer_one_stats, 'stats_two': golfer_two_stats,
               'scorecards': this_page_scorecard,
               'course_length': range(1, 10), 'all_golfers': all_golfers,
               'golfer_one': golfer_one, 'golfer_two': golfer_two,
               'record': record}
    return render(request, "golf/vs.html", context)


def post(request):
    """Lets the user post a match. Default to MCC White Tees"""
    if request.method == "POST":
        # Ensure user is logged in
        if not request.user.is_authenticated:
            message = 'You must be logged in to post a match.'
            return render(request, "golf/error.html", message)
        elif len(request.POST) not in [26, 48, 70, 92]:
            message = 'There was an error processing your request.'
            return render(request, "golf/error.html", {'message': message})
        else:
            # Determine golfer count
            golfer_count = 1
            golfer_scores = []
            if len(request.POST) == 48:
                golfer_count = 2
            if len(request.POST) == 70:
                golfer_count = 3
            if len(request.POST) == 92:
                golfer_count = 4
            # Parse all the scores
            for i in range(golfer_count):
                golfer_score = []
                golfer = request.POST[f'golfer-{i + 1}']
                if golfer == 'Golfer':
                    message = 'A golfer name was not selected.'
                    return render(request, "golf/error.html",
                                  {'message': message})
                golfer_score.append(golfer)
                for i in range(21):
                    # Ensure user submitted a valid integer
                    try:
                        this_score = int(request.POST[f'{golfer}-{i + 1}'])
                    except:
                        msg = 'All scores entered should be single numbers.'
                        return render(request, "golf/error.html",
                                      {'message': msg})
                    golfer_score.append(this_score)
                # Ensure front nine adds up
                if sum(golfer_score[1:10]) != golfer_score[10]:
                    message = f"{golfer}'s front nine scores do not add up."
                    return render(request, "golf/error.html",
                                  {'message': message})
                # Ensure back nine adds up
                elif sum(golfer_score[11:20]) != golfer_score[20]:
                    message = f"{golfer}'s back nine scores do not add up."
                    return render(request, "golf/error.html",
                                  {'message': message})
                # Clean up golfers scores
                golfer_score.pop(10)
                golfer_score.pop()
                golfer_score.pop()
                golfer_scores.append(golfer_score)

                # Ensure all scores are between 1 and 9
                for i in range(len(golfer_score)):
                    if i != 0:
                        if golfer_score[i] < 1 or golfer_score[i] > 9:
                            beginning = f"{golfer} has a hole score"
                            end = "less than 1 or greater than 9"
                            message = beginning + end
                            return render(request, "golf/error.html",
                                          {'message': message})
            # Store round information
            match = 0  # Default to match 0 for solo rounds
            # Create new match id
            if golfer_count != 1:
                highest_matches =  \
                    Round.objects.all().order_by('-match').values()
                highest_match = highest_matches[0]['match']
                match = highest_match + 1
            # Save a round for each golfer
            for i in range(len(golfer_scores)):
                golfer_name = golfer_scores[i][0]
                golfer = User.objects.get(first_name=golfer_name)
                course = Course.objects.get(
                    name=request.POST['course'], tees=request.POST['tees'])
                date = request.POST['round-date']
                round = Round(golfer=golfer, course=course,
                              date=date, match=match)
                round.save()
                # Store each score
                for j in range(1, len(golfer_scores[i])):
                    score = int(golfer_scores[i][j])
                    hole = Hole.objects.get(course=course, tee=j)
                    this_score = Score(
                        score=score, golfer=golfer, round=round, hole=hole)
                    this_score.save()
            # Return to home page
            return HttpResponseRedirect(reverse('index'))
    else:
        # Provide a form to post a match
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
        # Provide option drop down menu to switch golfer
        golfers = User.objects.exclude(pk=1)
        # Create default date as a placeholder date
        now = datetime.now()
        date = now.strftime("%Y-%m-%d")
        context = {"course_length": range(1, 10),
                   "course_names": course_names,
                   "golfers": golfers, "default_course": default_course,
                   "yardages": yardages, "handicaps": handicaps, 'pars': pars,
                   "available_tees": available_tees, "date": date}
        return render(request, "golf/post.html", context)


def post_course(request, name):
    """Allows the user to post a round or match. Default to white tees"""
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
    courses = Course.objects.all()
    course_names = []
    for course in courses:
        if course.name not in course_names:
            course_names.append(course.name)
    index = course_names.index(f'{name}')
    # Default to the requested course
    course_names.insert(0, course_names.pop(index))

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

    # Get the hole information for this course
    holes = Hole.objects.filter(course=default_course)
    yardages = []
    handicaps = []
    pars = []
    for i in range(len(holes)):
        yardages.append(holes[i].yardage)
        handicaps.append(holes[i].handicap)
        pars.append(holes[i].par)
    golfers = User.objects.exclude(pk=1)
    # Create default date as a placeholder date
    now = datetime.now()
    date = now.strftime("%Y-%m-%d")
    context = {"course_length": range(1, 10), "course_names": course_names,
               "golfers": golfers, "default_course": default_course,
               "yardages": yardages, 'handicaps': handicaps, "pars": pars,
               "available_tees": available_tees, "date": date}
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
                    message = "This tee option already" \
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
        courses = Course.objects.all()
        course_names = []
        for course in courses:
            if course.name not in course_names:
                course_names.append(course.name)
        context = {'course_names': course_names, "course_length": range(1, 10)}
        return render(request, "golf/new.html", context)


def edit(request, match_id):
    """Edits a match in the database"""
    if request.method == "POST":
        
    else:    
        # Retrieve match rounds
        rounds = Round.objects.filter(match=match_id)
        # Provide course names with the given course selected
        course_name = rounds[0].course.name
        course_tees = rounds[0].course.tees
        all_courses = Course.objects.all()
        course_names = []
        for course in all_courses:
            if course.name not in course_names:
                course_names.append(course.name)
        # Select the given course
        course_name_index = course_names.index(course_name)
        course_names.insert(0, course_names.pop(course_name_index))
        context = {'course_names': course_names}
        # Retrieve all golfers 
        all_golfers = User.objects.all()
        # Retrieve selected golfers  
        golfers = []
        for this_round in rounds:
            golfers.append(this_round.golfer)
        default_course = Course.objects.get(name=course_name,
                                            tees=course_tees)
        available_courses = Course.objects.filter(name=course_name)
        available_tees = []
        for i in range(len(available_courses)):
            available_tees.append(available_courses[i].tees)
        index = available_tees.index(f'{course_tees}')
        available_tees.insert(0, available_tees.pop(index))
        holes = Hole.objects.filter(course=default_course)
        yardages = []
        handicaps = []
        pars = []
        for i in range(len(holes)):
            yardages.append(holes[i].yardage)
            handicaps.append(holes[i].handicap)
            pars.append(holes[i].par)
        date = rounds[0].date
        date = date.strftime("%Y-%m-%d")
        # Get golfer strokes
        golfers_strokes = []
        for golfer_round in rounds:
            golfer_strokes = []
            golfer_scores = Score.objects.filter(round=golfer_round)
            for score in golfer_scores:
                golfer_strokes.append(score.score) 
            golfer_strokes.append(sum(golfer_strokes[9:]))
            golfer_strokes.append(sum(golfer_strokes[:-1]))
            golfer_strokes.insert(9, sum(golfer_strokes[:9]))
            golfer_strokes.insert(0, golfer_round.golfer.first_name)
            golfers_strokes.append(golfer_strokes)

            
        context = {"course_length": range(1, 10), "course_names": course_names,
               "golfers": golfers_strokes, "all_golfers": all_golfers, "default_course": default_course,
               "yardages": yardages, 'handicaps': handicaps, "pars": pars,
               "available_tees": available_tees, "date": date, "match_id": match_id}
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
