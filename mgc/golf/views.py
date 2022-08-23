from datetime import datetime
from decimal import MAX_EMAX
from distutils.sysconfig import get_python_lib
from re import M
from select import select
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse
from .models import User, Course, Hole, Score, Round

# Create your views here.
def index(request):
    all_stats = []
    all_golfers = []
    all_rounds = Round.objects.all()
    for round in all_rounds:
        if round.golfer not in all_golfers:
            all_golfers.append(round.golfer)
    for golfer in all_golfers:
        golfers_rounds = Round.objects.filter(golfer=golfer).exclude(match=0)
        stats = get_stats(golfers_rounds)
        all_stats.append(stats)
    def best_round(golfers_stats):
        return golfers_stats[2]
    all_stats.sort(key=best_round)
    return render(request, "golf/index.html", {'all_stats': all_stats})


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
    if request.method == "POST":
        # Ensure user is logged in
        if not request.user.is_authenticated:
            return render(request, "golf/error.html", {'message': 'You must be logged in to post a match.'})
        elif len(request.POST) not in [26, 48, 70, 92]:
            return render(request, "golf/error.html", {'message': 'There was an error processing your request.'})
        else:
            golfer_count = 1
            golfer_scores = []
            if len(request.POST) == 48: golfer_count = 2
            if len(request.POST) == 70: golfer_count = 3
            if len(request.POST) == 92: golfer_count = 4
            # Parse all the scores
            for i in range(golfer_count):
                golfer_score = []
                golfer = request.POST[f'golfer_{i + 1}']
                if golfer == 'Golfer':
                    return render(request, "golf/error.html", {'message': 'A golfer name was not selected.'})
                golfer_score.append(golfer)
                for i in range(21):
                    # Ensure user submitted a valid integer
                    try:
                        this_score = int(request.POST[f'{golfer}_{i + 1}'])
                    except:
                        return render(request, "golf/error.html", {'message': 'All scores entered should be single numbers.'})
                    golfer_score.append(this_score)
                if sum(golfer_score[1:10]) != golfer_score[10]:
                    return render(request, "golf/error.html", {'message': f"{golfer}'s front nine scores do not add up."})
                elif sum(golfer_score[11:20]) != golfer_score[20]:
                    return render(request, "golf/error.html", {'message': f"{golfer}'s back nine scores do not add up."})
                golfer_score.pop(10)
                golfer_score.pop()
                golfer_score.pop()
                golfer_scores.append(golfer_score)

                # Ensure all scores are between 1 and 9
                for i in range(len(golfer_score)):
                    if i != 0:
                        if golfer_score[i] < 1 or golfer_score[i] > 9:
                            return render(request, "golf/error.html", {'message': f"{golfer} has a hole score less than 1 or greater than 9"})
            # Store round information
            match = 0 # Default to match 0 for solo rounds
            # Create new match id
            if golfer_count != 1:
                highest_matches = Round.objects.all().order_by('-match').values()
                highest_match = highest_matches[0]['match']
                match = highest_match + 1
            for i in range(len(golfer_scores)):
                golfer_name = golfer_scores[i][0]
                golfer = User.objects.get(first_name=golfer_name)
                course = Course.objects.get(name=request.POST['course'], tees=request.POST['tees'])
                date = request.POST['round_date']
                round = Round(golfer=golfer, course=course, date=date, match=match)
                round.save()
                # Store each score
                for j in range(1, len(golfer_scores[i])):
                    score = int(golfer_scores[i][j])
                    hole = Hole.objects.get(course=course, tee=j)
                    this_score = Score(score=score, golfer=golfer, round=round, hole=hole)
                    this_score.save()

            return HttpResponseRedirect(reverse('index')) # Return to home page
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
        golfers = User.objects.exclude(pk=1) # Provide option drop down menu to switch golfer
        # Create default date as a placeholder date
        now = datetime.now()
        date = now.strftime("%Y-%m-%d")
        context = {"course_length": range(1, 10), "course_names": course_names, 'golfers': golfers, 'default_course': default_course,'yardages': yardages, 'handicaps': handicaps, 'pars': pars, 'available_tees': available_tees, 'date': date}
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
        # Otherwise choose first non white tee
        url = reverse('post_tees', kwargs={'name': name, 'tees': courses[0].tees})
        return HttpResponseRedirect(url) 


def post_tees(request, name, tees):
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
    context = {"course_length": range(1, 10), "course_names": course_names, 'golfers': golfers, 'default_course': default_course,'yardages': yardages, 'handicaps': handicaps, 'pars': pars, 'available_tees': available_tees, 'date': date}
    return render(request, "golf/post.html", context)

def new(request):
    if request.method == "POST":
        # Verify and store all course information
        # Verify valid slope and course rating input
        try:
            slope = int(request.POST['slope'])
        except:
            return render(request, "golf/error.html", {'message': 'Invalid Slope Rating'})
        if slope < 55 or slope > 155:
            return render(request, "golf/error.html", {'message': 'Invalid Slope Rating'})
        try:
            rating = float(request.POST['rating'])
        except:
            return render(request, "golf/error.html", {'message': 'Invalid Course Rating'})
        test_rating = str(rating)
        if len(test_rating) != 4:
            return render(request, "golf/error.html", {'message': 'Invalid Course Rating'})
        for i in range(len(test_rating)):
            if i != 2:
                if not test_rating[i].isdigit():
                    return render(request, "golf/error.html", {'message': 'Invalid Course Rating'})
            else:
                if test_rating[i] != '.':
                    return render(request, "golf/error.html", {'message': 'Invalid Course Rating'})
        if rating < 60 or rating > 81:
            return render(request, "golf/error.html", {'message': 'Invalid Course Rating'})

        # Store yardage information
        yardages = []
        for i in range(1, 19):
            this_yardage = int(request.POST[f"yardages_{i}"])
            if this_yardage < 50 or this_yardage > 999:
                return render(request, "golf/error.html", {'message': 'No hole should have a yardage less than 50 or greater than 999'})
            yardages.append(this_yardage)
        # Verify math adds up
        if sum(yardages[0:9]) != int(request.POST['yardages_front']):
            return render(request, "golf/error.html", {'message': 'The front nine yardages do not add up to the front nine yardage total.'})
        elif sum(yardages[9:]) != int(request.POST['yardages_back']):
            return render(request, "golf/error.html", {'message': 'The back nine yardages do not add up to the back nine yardage total.'})
        elif sum(yardages) != int(request.POST['yardages_total']):
             return render(request, "golf/error.html", {'message': 'The yardages by hole do not add up to the yardage total.'})

        # Store par information
        pars = []
        for i in range(1, 19):
            this_par = int(request.POST[f"par_{i}"])
            if this_par < 3 or this_par > 5:
                return render(request, "golf/error.html", {'message': 'No hole should have a par less than 3 or greater than 5'})
            pars.append(this_par)
        # Verify math adds up
        if sum(pars[0:9]) != int(request.POST['par_front']):
            return render(request, "golf/error.html", {'message': 'The front nine pars do not add up to the front nine par total.'})
        elif sum(pars[9:]) != int(request.POST['par_back']):
            return render(request, "golf/error.html", {'message': 'The back nine pars do not add up to the back nine par total.'})
        elif sum(pars) != int(request.POST['par_total']):
             return render(request, "golf/error.html", {'message': 'The pars by hole do not add up to the par total.'})
        
        # Store handicap information
        handicaps = []
        for i in range(1, 19):
            this_handicap = int(request.POST[f"handicap_{i}"])
            if this_handicap < 1 or this_handicap > 18:
                return render(request, "golf/error.html", {'message': 'No hole should have a handicap rating less than 1 or greater than 18'})
            handicaps.append(this_handicap)
        # Check if there are any duplicates
        if len(handicaps) != len(set(handicaps)):
            return render(request, "golf/error.html", {'message': 'Multiple holes cannot have the same handicap.'})
        
        # Check if the user is adding a new course or just a new tee option
        # User is adding a new course
        if request.POST['course-or-tees'] == 'Course':
            # Check if the course name already exists
            all_courses = Course.objects.all()
            for i in range(len(all_courses)):
                if all_courses[i].name == request.POST['new_course_name']:
                    return render(request, "golf/error.html", {'message': 'A course with this name already exists.'})
            
            # Add Course
            course_abbreviation = course_abbreviate(request.POST['new_course_name'])
            this_course = Course(name=request.POST['new_course_name'], tees=request.POST['new_tees'], front_par=int(request.POST['par_front']), back_par=int(request.POST['par_back']), par=int(request.POST['par_total']), front_yardage=int(request.POST['yardages_front']), back_yardage=int(request.POST['yardages_back']), yardage=int(request.POST['yardages_total']), slope=slope, course_rating=rating, abbreviation=course_abbreviation)
            this_course.save()
            for i in range(18):
                this_hole = Hole(course=this_course, tee=i+1, par=pars[i], yardage=yardages[i], handicap=handicaps[i])
                this_hole.save()
            return HttpResponseRedirect(reverse('index'))
        # User is just adding a new tee option
        elif request.POST['course-or-tees'] == 'Tees':
            # Check if tee option already exists for the selected course
            all_courses = Course.objects.all()
            for course in all_courses:
                if course.name == request.POST['course_exists'] and course.tees == request.POST['tees_course_exists']:
                    return render(request, "golf/error.html", {'message': 'This tee option already exists for the selected course.'})
            
            # Add Course
            course_abbreviation = course_abbreviate(request.POST['new_course_name'])
            this_course = Course(name=request.POST['course_exists'], tees=request.POST['tees_course_exists'], front_par=int(request.POST['par_front']), back_par=int(request.POST['par_back']), par=int(request.POST['par_total']), front_yardage=int(request.POST['yardages_front']), back_yardage=int(request.POST['yardages_back']), yardage=int(request.POST['yardages_total']), slope=slope, course_rating=rating, abbreviation=course_abbreviation)
            this_course.save()
            for i in range(18):
                this_hole = Hole(course=this_course, tee=i+1, par=pars[i], yardage=yardages[i], handicap=handicaps[i])
                this_hole.save()
            return HttpResponseRedirect(reverse('index'))
        else:
            # Return an error
            return render(request, "golf/error.html", {'message': 'An unexpected error occured. Please try again.'})
    else:
        # Display form
        courses = Course.objects.all()
        course_names = []
        for course in courses:
            if course.name not in course_names:
                course_names.append(course.name)
        
        return render(request, "golf/new.html", {'course_names': course_names, "course_length": range(1, 10)})

def golfer(request, golfer):
    this_golfer = User.objects.get(first_name=golfer)
    golfer_rounds = Round.objects.filter(golfer=this_golfer).order_by('-date')
    stats = get_stats(golfer_rounds)
    scorecards = []
    all_golfers = []
    all_rounds = Round.objects.all()
    for round in all_rounds:
        if round.golfer not in all_golfers:
            all_golfers.append(round.golfer)
    for this_round in golfer_rounds:
        scorecard = get_scorecard(this_round)
        scorecards.append(scorecard)
    return render(request, "golf/golfer.html", {'stats': stats, 'scorecards': scorecards, 'golfer': this_golfer, 'course_length': range(1, 10), 'all_golfers': all_golfers})

def get_course_avg_scorecard(rounds):
    handicaps = []
    pars = []
    hole_sum = [0] * 18
    to_pars = []
    hole_scores = []
    yardages = []
    course = rounds[0].course
    holes = Hole.objects.filter(course=course).order_by('tee')
    for i in range(len(holes)):
        yardages.append(holes[i].yardage)
        handicaps.append(holes[i].handicap)
        pars.append(holes[i].par)
    
    for this_round in rounds:
        scores = Score.objects.filter(round=this_round)
        for i in range(len(scores)):
            hole_sum[i] += scores[i].score
    
    strokes = []
    for i in range(len(hole_sum)):
        hole_avg = round(hole_sum[i] / len(rounds), 1)
        strokes.append(hole_avg)
            
    
    
    par_tracker = 0 
    for i in range(9):
        to_this_par = strokes[i] - pars[i]
        if to_this_par == 0:
            to_pars.append(par_shift(par_tracker))
        else:
            par_tracker += to_this_par
            to_pars.append(par_shift(par_tracker))
    par_tracker = 0 
    for i in range(9):
        to_this_par = strokes[i + 9] - pars[i + 9]
        if to_this_par == 0:
            to_pars.append(par_shift(par_tracker))
        else:
            par_tracker += to_this_par
            to_pars.append(par_shift(par_tracker))
    front_nine_to_par = par_shift(sum(strokes[:9]) - sum(pars[:9]))
    back_nine_to_par = par_shift(sum(strokes[9:]) - sum(pars[9:])) 
    total_to_par = par_shift(sum(strokes) - sum(pars))  
    to_pars.append(back_nine_to_par)
    to_pars.append(total_to_par) 
    to_pars.insert(9, front_nine_to_par) 
    for i in range(len(strokes)):
        this_score = round(strokes[i] - pars[i])
        hole_scores.append(this_score)
    strokes.append(sum(strokes[9:]))
    strokes.append(sum(strokes[:-1]))
    strokes.insert(9, sum(strokes[:9]))
    hole_scores.append('NA')
    hole_scores.append('NA')
    hole_scores.insert(9, 'NA')
    zipped_scores = zip(strokes, hole_scores)                                                                                                                                                                                                                                             
    scorecard = {'course': course, 'yardages': yardages, 'handicaps': handicaps, 'pars': pars, 'strokes': strokes, 'to_pars': to_pars, 'zipped_scores': zipped_scores}
    return scorecard

def vs(request, golfer1, golfer2):
    all_golfers = User.objects.all()
    golfer_one = User.objects.get(first_name=golfer1)
    golfer_two = User.objects.get(first_name=golfer2)
    golfer_one_rounds = Round.objects.filter(golfer=golfer_one)
    golfer_two_rounds = Round.objects.filter(golfer=golfer_two)
    golfer_one_match_ids = []
    golfer_two_match_ids = []
    for this_round in golfer_one_rounds:
        if this_round.match not in golfer_one_match_ids: golfer_one_match_ids.append(this_round.match)
    for this_round in golfer_two_rounds:
        if this_round.match not in golfer_two_match_ids: golfer_two_match_ids.append(this_round.match)
    cumulative_match_ids = []
    for id in golfer_one_match_ids:
        if id in golfer_two_match_ids: cumulative_match_ids.append(id)
    golfer_one_rounds = Round.objects.filter(golfer=golfer_one, match__in=cumulative_match_ids).order_by('-date')
    golfer_two_rounds = Round.objects.filter(golfer=golfer_two, match__in=cumulative_match_ids).order_by('-date')
    if len(golfer_one_rounds) == 0:
        return render(request, "golf/error.html", {'message': 'The selected golfers have not played each other.'})
    golfer_one_stats = get_stats(golfer_one_rounds)
    golfer_two_stats = get_stats(golfer_two_rounds)
    both_golfers_rounds = [golfer_one_rounds, golfer_two_rounds]
    scorecards = get_vs_scorecards(both_golfers_rounds)
    if golfer_one_stats[2] > golfer_two_stats[2]:
        buffer = golfer_one_stats
        golfer_one_stats = golfer_two_stats
        golfer_two_stats = buffer
    
    match_checker = {'golfer_one_wins': 0, 'golfer_two_wins': 0, 'ties': 0}
    for scorecard in scorecards:
        if scorecard['strokes_one'][-1] > scorecard['strokes_two'][-1]:
            match_checker['golfer_one_wins'] += 1
        elif scorecard['strokes_one'][-1] < scorecard['strokes_two'][-1]:
            match_checker['golfer_two_wins'] += 1
        else:
            match_checker['ties'] += 1
    
    if match_checker['golfer_one_wins'] >= match_checker['golfer_two_wins']:
        record = f"{golfer_one} is {match_checker['golfer_one_wins']}-{match_checker['golfer_two_wins']}-{match_checker['ties']} vs {golfer_two}"
    else:
        record = f"{golfer_two} is {match_checker['golfer_two_wins']}-{match_checker['golfer_one_wins']}-{match_checker['ties']} vs {golfer_one}"
 
    return render(request, "golf/vs.html", {'stats_one': golfer_one_stats, 'stats_two': golfer_two_stats, 'scorecards': scorecards, 'course_length': range(1, 10), 'all_golfers': all_golfers, 'golfer_one': golfer_one, 'golfer_two': golfer_two, 'record': record})

def get_vs_scorecards(golfer_rounds):
    scorecards = []
    golfer_one_rounds = golfer_rounds[0]
    golfer_two_rounds = golfer_rounds[1]

    for i in range(len(golfer_one_rounds)):
        round = golfer_one_rounds[i]
        handicaps = []
        pars = []
        yardages = []
        strokes_one = []
        strokes_two = []
        scores_one = []
        scores_two = []
        to_pars_one = []
        to_pars_two = []
        course = golfer_one_rounds[i].course
        holes = Hole.objects.filter(course=course).order_by('tee')
        scores_per_hole_one = Score.objects.filter(round=golfer_one_rounds[i])
        scores_per_hole_two = Score.objects.filter(round=golfer_two_rounds[i])
        for i in range(len(holes)):
            yardages.append(holes[i].yardage)
            handicaps.append(holes[i].handicap)
            pars.append(holes[i].par)
            strokes_one.append(scores_per_hole_one[i].score)
            scores_one.append(scores_per_hole_one[i].score - holes[i].par)
            strokes_two.append(scores_per_hole_two[i].score)
            scores_two.append(scores_per_hole_two[i].score - holes[i].par)
        par_tracker_one = 0
        par_tracker_two = 0
        for i in range(9):
            if scores_one[i] == 0:
                to_pars_one.append(par_shift(par_tracker_one))
            else:
                par_tracker_one += scores_one[i]
                to_pars_one.append(par_shift(par_tracker_one))
            if scores_two[i] == 0:
                to_pars_two.append(par_shift(par_tracker_two))
            else:
                par_tracker_two += scores_two[i]
                to_pars_two.append(par_shift(par_tracker_two))
        par_tracker_one = 0
        par_tracker_two = 0
        for i in range(9):
            if scores_one[i + 9] == 0:
                to_pars_one.append(par_shift(par_tracker_one))
            else:
                par_tracker_one += scores_one[i + 9]
                to_pars_one.append(par_shift(par_tracker_one))
            if scores_two[i + 9] == 0:
                to_pars_two.append(par_shift(par_tracker_two))
            else:
                par_tracker_two += scores_two[i + 9]
                to_pars_two.append(par_shift(par_tracker_two))
        front_nine_to_par_one = par_shift(sum(strokes_one[:9]) - sum(pars[:9]))
        front_nine_to_par_two = par_shift(sum(strokes_two[:9]) - sum(pars[:9]))
        back_nine_to_par_one = par_shift(sum(strokes_one[9:]) - sum(pars[9:]))
        back_nine_to_par_two = par_shift(sum(strokes_two[9:]) - sum(pars[9:]))
        total_to_par_one = par_shift(sum(strokes_one) - sum(pars))
        total_to_par_two = par_shift(sum(strokes_two) - sum(pars))
        to_pars_one.append(back_nine_to_par_one)
        to_pars_two.append(back_nine_to_par_two)
        to_pars_one.append(total_to_par_one)
        to_pars_two.append(total_to_par_two)
        to_pars_one.insert(9, front_nine_to_par_one)
        to_pars_two.insert(9, front_nine_to_par_two)
        strokes_one.append(sum(strokes_one[9:]))
        strokes_two.append(sum(strokes_two[9:]))
        strokes_one.append(sum(strokes_one[:-1]))
        strokes_two.append(sum(strokes_two[:-1]))
        strokes_one.insert(9, sum(strokes_one[:9]))
        strokes_two.insert(9, sum(strokes_two[:9]))
        scores_one.append('NA')
        scores_one.append('NA')
        scores_two.append('NA')
        scores_two.append('NA')
        scores_one.insert(9, 'NA')
        scores_two.insert(9, 'NA')
        zipped_scores_one = zip(strokes_one, scores_one)
        zipped_scores_two = zip(strokes_two, scores_two)
        scorecard = {'round': round, 'course': course, 'yardages': yardages, 'handicaps': handicaps, 'pars': pars, 'strokes_one': strokes_one, 'strokes_two': strokes_two, 'to_pars_one': to_pars_one, 'to_pars_two': to_pars_two, 'zipped_scores_one': zipped_scores_one, 'zipped_scores_two': zipped_scores_two}
        scorecards.append(scorecard)
    return scorecards
            


def get_scorecard(round):
    handicaps = []
    pars = []
    strokes = []
    to_pars = []
    hole_scores = []
    yardages = []
    course = round.course
    holes = Hole.objects.filter(course=course).order_by('tee')
    scores = Score.objects.filter(round=round)
    for i in range(len(holes)):
        yardages.append(holes[i].yardage)
        handicaps.append(holes[i].handicap)
        pars.append(holes[i].par)
        strokes.append(scores[i].score)
        hole_scores.append(scores[i].score - holes[i].par)
    par_tracker = 0 
    for i in range(9):
        to_this_par = strokes[i] - pars[i]
        if to_this_par == 0:
            to_pars.append(par_shift(par_tracker))
        else:
            par_tracker += to_this_par
            to_pars.append(par_shift(par_tracker))
    par_tracker = 0 
    for i in range(9):
        to_this_par = strokes[i + 9] - pars[i + 9]
        if to_this_par == 0:
            to_pars.append(par_shift(par_tracker))
        else:
            par_tracker += to_this_par
            to_pars.append(par_shift(par_tracker))
    front_nine_to_par = par_shift(sum(strokes[:9]) - sum(pars[:9]))
    back_nine_to_par = par_shift(sum(strokes[9:]) - sum(pars[9:])) 
    total_to_par = par_shift(sum(strokes) - sum(pars))  
    to_pars.append(back_nine_to_par)
    to_pars.append(total_to_par) 
    to_pars.insert(9, front_nine_to_par) 
    strokes.append(sum(strokes[9:]))
    strokes.append(sum(strokes[:-1]))
    strokes.insert(9, sum(strokes[:9]))
    hole_scores.append('NA')
    hole_scores.append('NA')
    hole_scores.insert(9, 'NA')
    zipped_scores = zip(strokes, hole_scores)                                                                                                                                                                                                                                             
    scorecard = {'round': round, 'course': course, 'yardages': yardages, 'handicaps': handicaps, 'pars': pars, 'strokes': strokes, 'to_pars': to_pars, 'zipped_scores': zipped_scores}
    return scorecard

def course(request, course, tees, golfer):
    all_golfers = User.objects.all()
    courses = Course.objects.all()
    course_names = []
    for each_course in courses:
        if each_course.name not in course_names:
            course_names.append(each_course.name)
    selected_course_index = course_names.index(course)
    if selected_course_index != 0: course_names.insert(0, course_names.pop(selected_course_index))
    tee_options = []
    duplicate_courses = Course.objects.filter(name=course)
    for course in duplicate_courses:
        tee_options.append(course.tees)
    selected_tee_index = tee_options.index(tees)
    if selected_tee_index != 0: tee_options.insert(0, tee_options.pop(selected_tee_index))
    course = Course.objects.get(name=course, tees=tees)
    golfer = User.objects.get(first_name=golfer)
    rounds = Round.objects.filter(golfer=golfer, course=course).order_by('-date')
    if len(rounds) == 0:
        return render(request, "golf/error.html", {'message': 'The selected golfer has not played the selected course'})
    
    scorecards = []
    for round in rounds:
        scorecard = get_scorecard(round)
        scorecards.append(scorecard)
    stats = get_stats(rounds)
    avg_scorecard = get_course_avg_scorecard(rounds)
    return render(request, "golf/course.html", {'stats': stats, 'avg_scorecard': avg_scorecard, 'scorecards': scorecards, 'courses': course_names, 'tees': tee_options, 'golfer': golfer, 'course_length': range(1, 10), 'all_golfers': all_golfers})


def par_shift(score):
    if score >= 1: return f"+{score}"
    elif score == 0: return "E"
    else: return str(score)

def get_stats(rounds):
    round_amount = len(rounds)
    golfer = rounds[0].golfer
    total_scores = 0
    score_tracker = {'eagle_counter': 0, 'birdie_counter': 0, 'par_counter': 0, 'bogey_counter': 0, 'double_bogey_counter': 0, 'triple_bogey_counter': 0, 'max_counter': 0, 'best_score': 300, 'par_three_counter': 0, 'par_four_counter': 0, 'par_five_counter': 0, 'par_three_sum': 0, 'par_four_sum': 0, 'par_five_sum': 0}
    for each_round in rounds:
        round_holes = Score.objects.filter(round=each_round)
        round_score = 0
        for hole in round_holes:
            this_score = hole.score - hole.hole.par
            total_scores += hole.score - hole.hole.par
            round_score += hole.score - hole.hole.par
            if this_score <= -2: score_tracker['eagle_counter'] += 1
            elif this_score == -1: score_tracker['birdie_counter'] += 1
            elif this_score == 0: score_tracker['par_counter'] += 1
            elif this_score == 1: score_tracker['bogey_counter'] += 1
            elif this_score == 2: score_tracker['double_bogey_counter'] += 1
            elif this_score == 3: score_tracker['triple_bogey_counter'] += 1
            elif this_score > 3: score_tracker['max_counter'] += 1
            if hole.hole.par == 3: 
                score_tracker['par_three_counter'] += 1
                score_tracker['par_three_sum'] += this_score
            elif hole.hole.par == 4:
                score_tracker['par_four_counter'] += 1
                score_tracker['par_four_sum'] += this_score
            else:
                score_tracker['par_five_counter'] += 1
                score_tracker['par_five_sum'] += this_score
        if round_score < score_tracker['best_score']: 
            score_tracker['best_score'] = round_score
    best_score = score_tracker['best_score'] + 72
    best_score_to_par = par_shift(score_tracker['best_score'])
    best_score = f"{best_score_to_par} ({best_score})"
    avg_par = round(total_scores / round_amount, 2)
    avg_score = round(avg_par + 72, 2)
    avg_par = par_shift(avg_par)
    eagles = score_tracker['eagle_counter']
    birdies_per = round(score_tracker['birdie_counter'] / round_amount, 2)
    pars_per = round(score_tracker['par_counter'] / round_amount, 2)
    bogeys_per = round(score_tracker['bogey_counter'] / round_amount, 2)
    doubles_per = round(score_tracker['double_bogey_counter'] / round_amount, 2)
    triples_per = round(score_tracker['triple_bogey_counter'] / round_amount, 2)
    maxes_per = round(score_tracker['max_counter'] / round_amount, 2)
    par_three_average = round((score_tracker['par_three_sum'] / score_tracker['par_three_counter']) + 3, 2)
    par_four_average = round((score_tracker['par_four_sum'] / score_tracker['par_four_counter']) + 4, 2)
    par_five_average = round((score_tracker['par_five_sum'] / score_tracker['par_five_counter']) + 5, 2)
     
    golfer_stats = [golfer, round_amount, avg_score, avg_par, best_score, birdies_per, pars_per, bogeys_per, doubles_per, triples_per, maxes_per, par_three_average, par_four_average, par_five_average, eagles]

    return golfer_stats

def course_abbreviate(course_name):
    abbreviation = course_name[0]
    for i in range(1, len(course_name)):
        if course_name[i - 1] == ' ':
            abbreviation += course_name[i]
    abbreviation = abbreviation.upper()
    return abbreviation

def page_not_found_view(request, exception):
    return render(request, "golf/error.html", {'message': 'Page Not Found'})