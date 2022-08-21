from datetime import datetime
from re import M
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse
from .models import User, Course, Hole, Score, Round

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
            this_course = Course(name=request.POST['new_course_name'], tees=request.POST['new_tees'], front_par=int(request.POST['par_front']), back_par=int(request.POST['par_back']), par=int(request.POST['par_total']), front_yardage=int(request.POST['yardages_front']), back_yardage=int(request.POST['yardages_back']), yardage=int(request.POST['yardages_total']), slope=slope, course_rating=rating)
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
            this_course = Course(name=request.POST['course_exists'], tees=request.POST['tees_course_exists'], front_par=int(request.POST['par_front']), back_par=int(request.POST['par_back']), par=int(request.POST['par_total']), front_yardage=int(request.POST['yardages_front']), back_yardage=int(request.POST['yardages_back']), yardage=int(request.POST['yardages_total']), slope=slope, course_rating=rating)
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
    stats = get_stats(golfer)
    scorecards = []
    all_golfers = []
    all_rounds = Round.objects.all()
    for round in all_rounds:
        if round.golfer not in all_golfers:
            all_golfers.append(round.golfer)
    this_golfer = User.objects.get(first_name=golfer)
    golfer_rounds = Round.objects.filter(golfer=this_golfer)
    for this_round in golfer_rounds:
        handicaps = []
        pars = []
        strokes = []
        to_pars = []
        hole_scores = []
        yardages = []
        course = this_round.course
        holes = Hole.objects.filter(course=course).order_by('tee')
        scores = Score.objects.filter(round=this_round)
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
        scorecard = {'round': this_round, 'course': course, 'yardages': yardages, 'handicaps': handicaps, 'pars': pars, 'strokes': strokes, 'to_pars': to_pars, 'zipped_scores': zipped_scores}
        scorecards.append(scorecard)
    return render(request, "golf/golfer.html", {'scorecards': scorecards, 'golfer': this_golfer, 'course_length': range(1, 10), 'all_golfers': all_golfers})

def par_shift(score):
    if score >= 1: return f"+{score}"
    elif score == 0: return "E"
    else: return str(score)

def get_stats(golfer):
    golfer = User.objects.get(first_name=golfer)
    golfer_rounds = Round.objects.filter(golfer=golfer)
    rounds = len(golfer_rounds)
    golfer_holes = []
    difference = 0
    for round in golfer_rounds:
        round_holes = Score.objects.filter(round=round)
        golfer_holes.append(round_holes)
    score_tracker = {'eagle_counter': 0, 'birdie_counter': 0, 'par_counter': 0, 'bogey_counter': 0, 'double_bogey_counter': 0, 'triple_bogey_counter': 0, 'max_counter': 0, 'best_score': 300}
    for i in range(len(golfer_holes)):
        round_score = 0
        for j in range(len(golfer_holes[i])):
            difference += golfer_holes[i][j].score - golfer_holes[i][j].hole.par
            round_score += golfer_holes[i][j].score - golfer_holes[i][j].hole.par
            if difference <= -2: score_tracker['eagle_counter'] += 1
            if difference == -1: score_tracker['birdie_counter'] += 1
            if difference == 0: score_tracker['par_counter'] += 1
            if difference == 1: score_tracker['bogey_counter'] += 1
            if difference == 2: score_tracker['double_bogey_counter'] += 1
            if difference == 3: score_tracker['triple_bogey_counter'] += 1
            if difference > 3: score_tracker['max_counter'] += 1
        if round_score < score_tracker['best_score']: 
            round_score = par_shift(round_score + 72)
            score_tracker['best_score'] = round_score

    avg_par = difference / rounds
    avg_score = avg_par + 72
    avg_par = par_shift(avg_par)
    eagles = score_tracker['eagle_counter']
    birdies_per = score_tracker['birdie_counter'] / rounds
    pars_per = score_tracker['par_counter'] / rounds
    bogeys_per = score_tracker['bogey_counter'] / rounds
    doubles_per = score_tracker['double_bogey_counter'] / round_score
    triples_per = score_tracker['triple_bogey_counter'] / round_score
    maxes_per = score_tracker['max_counter'] / round_score
    # par_3_avg = 
    # par_4_avg =
    # par_5_avg = 

    return 1
