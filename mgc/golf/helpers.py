from .models import Score, Hole, Course, Round, User
from datetime import datetime
from django.db.models import F


def abbreviate_course(course_name: str) -> str:
    """Abbreviates a course name"""
    abbreviation = course_name[0]
    for i in range(1, len(course_name)):
        if course_name[i - 1] == ' ':
            abbreviation += course_name[i]
    abbreviation = abbreviation.upper()
    return abbreviation


def par_shift(score: int) -> str:
    """Shift an integer score to a readable golf score"""
    if score > 0:
        return f"+{score}"
    elif score == 0:
        return "E"
    else:
        return str(score)


def get_stats(rounds):
    """Returns a stat line based on rounds given (queryset)"""
    round_amount = len(rounds)  # Amount of rounds for math
    golfer = rounds[0].golfer  # Golfer who owns these rounds
    # Count data based on round information
    total_scores = 0
    score_tracker = {'eagle_counter': 0, 'birdie_counter': 0,
                     'par_counter': 0, 'bogey_counter': 0,
                     'double_bogey_counter': 0, 'triple_bogey_counter': 0,
                     'max_counter': 0, 'best_score': 300,
                     'par_three_counter': 0, 'par_four_counter': 0,
                     'par_five_counter': 0, 'par_three_sum': 0,
                     'par_four_sum': 0, 'par_five_sum': 0}
    for each_round in rounds:
        round_holes = Score.objects.filter(round=each_round)
        round_score = 0
        for hole in round_holes:
            this_score = hole.score - hole.hole.par
            total_scores += hole.score - hole.hole.par  # Update total scores
            round_score += hole.score - hole.hole.par  # Update round score
            # Update score tracker for the type of score
            if this_score <= -2:
                score_tracker['eagle_counter'] += 1
            elif this_score == -1:
                score_tracker['birdie_counter'] += 1
            elif this_score == 0:
                score_tracker['par_counter'] += 1
            elif this_score == 1:
                score_tracker['bogey_counter'] += 1
            elif this_score == 2:
                score_tracker['double_bogey_counter'] += 1
            elif this_score == 3:
                score_tracker['triple_bogey_counter'] += 1
            elif this_score > 3:
                score_tracker['max_counter'] += 1
            # Update score tracker for the type of hole
            if hole.hole.par == 3:
                score_tracker['par_three_counter'] += 1
                score_tracker['par_three_sum'] += this_score
            elif hole.hole.par == 4:
                score_tracker['par_four_counter'] += 1
                score_tracker['par_four_sum'] += this_score
            else:
                score_tracker['par_five_counter'] += 1
                score_tracker['par_five_sum'] += this_score
        # Replace best round if applicable
        if round_score < score_tracker['best_score']:
            score_tracker['best_score'] = round_score
    # Calc stats
    best_score = score_tracker['best_score'] + 72  # Calc best score
    best_score_to_par = par_shift(
        score_tracker['best_score'])  # Calc best score to par
    best_score = f"{best_score_to_par} ({best_score})"
    avg_par = round(total_scores / round_amount)  # Calc average par
    avg_score = round(avg_par + 72)  # Calc average score
    avg_par = par_shift(avg_par)  # Calc average par
    eagles = score_tracker['eagle_counter']  # Count eagles
    # Calc score types per round
    birdies_per = round(score_tracker['birdie_counter'] / round_amount, 2)
    pars_per = round(score_tracker['par_counter'] / round_amount, 2)
    bogeys_per = round(score_tracker['bogey_counter'] / round_amount, 2)
    doubles_per = round(
        score_tracker['double_bogey_counter'] / round_amount, 2)
    triples_per = round(
        score_tracker['triple_bogey_counter'] / round_amount, 2)
    maxes_per = round(score_tracker['max_counter'] / round_amount, 2)
    # Calc strokes averages per hole type
    par_three_sum = score_tracker['par_three_sum']
    par_three_counter = score_tracker['par_three_counter']
    par_four_sum = score_tracker['par_four_sum']
    par_four_counter = score_tracker['par_four_counter']
    par_five_sum = score_tracker['par_five_sum']
    par_five_counter = score_tracker['par_five_counter']
    par_three_average = round((par_three_sum / par_three_counter) + 3, 2)
    par_four_average = round((par_four_sum / par_four_counter) + 4, 2)
    par_five_average = round((par_five_sum / par_five_counter) + 5, 2)
    # Create list of stats to be returned
    golfer_stats = [golfer.first_name, round_amount, avg_score, avg_par, best_score,
                    birdies_per, pars_per, bogeys_per, doubles_per,
                    triples_per, maxes_per, par_three_average,
                    par_four_average, par_five_average, eagles]
    return golfer_stats


def get_scorecard(round) -> list:
    """Returns a scorecard for a round (queryset)"""
    # Create a list for each row in the scorecard
    match_id = round.match
    handicaps = []
    pars = []
    strokes = []
    hole_scores = []
    yardages = []
    course = round.course  # Get course
    holes = Hole.objects.filter(course=course).order_by(
        'tee')  # Get course holes
    scores = Score.objects.filter(round=round)  # Get round scores
    # Update each row of the scorecard based on course holes and round scores
    for i in range(len(holes)):
        yardages.append(holes[i].yardage)
        handicaps.append(holes[i].handicap)
        pars.append(holes[i].par)
        strokes.append(scores[i].score)
        hole_scores.append(scores[i].score - holes[i].par)
    to_pars = get_to_pars(strokes, pars)  # Calculate golfers to pars
    # Total strokes
    strokes.append(sum(strokes[9:]))
    strokes.append(sum(strokes[:-1]))
    strokes.insert(9, sum(strokes[:9]))
    # Total holes_scores
    hole_scores += ['NA', 'NA']
    hole_scores.insert(9, 'NA')
    zipped_scores = zip(strokes, hole_scores)  # Zip scores for rendering
    scorecard = {'round': round, 'course': course, 'yardages': yardages,
                 'handicaps': handicaps, 'pars': pars, 'strokes': strokes,
                 'to_pars': to_pars, 'match_id': match_id, 'zipped_scores': zipped_scores}
    return scorecard


def get_vs_scorecards(golfer_rounds) -> list:
    """Returns all 'vs' scorecards for rounds between two golfers"""
    scorecards = []
    # Get golfer rounds
    golfer_one_rounds = golfer_rounds[0]
    golfer_two_rounds = golfer_rounds[1]
    for i in range(len(golfer_one_rounds)):  # For each match / pair of rounds
        # Create a list for each row in the scorecard
        round = golfer_one_rounds[i]
        handicaps = []
        pars = []
        yardages = []
        strokes_one = []
        strokes_two = []
        scores_one = []
        scores_two = []
        course = golfer_one_rounds[i].course
        holes = Hole.objects.filter(course=course).order_by(
            'tee')  # Get hole information for the course
        # Get scores for both golfers in this match
        scores_per_hole_one = Score.objects.filter(round=golfer_one_rounds[i])
        scores_per_hole_two = Score.objects.filter(round=golfer_two_rounds[i])
        # Update row's of the scorecard based on course holes and round scores
        for i in range(len(holes)):
            yardages.append(holes[i].yardage)
            handicaps.append(holes[i].handicap)
            pars.append(holes[i].par)
            strokes_one.append(scores_per_hole_one[i].score)
            scores_one.append(scores_per_hole_one[i].score - holes[i].par)
            strokes_two.append(scores_per_hole_two[i].score)
            scores_two.append(scores_per_hole_two[i].score - holes[i].par)
        # Calculate to pars for both golfers
        to_pars_one = get_to_pars(strokes_one, pars)
        to_pars_two = get_to_pars(strokes_two, pars)
        # Total strokes for both golfers
        strokes_one.append(sum(strokes_one[9:]))
        strokes_two.append(sum(strokes_two[9:]))
        strokes_one.append(sum(strokes_one[:-1]))
        strokes_two.append(sum(strokes_two[:-1]))
        strokes_one.insert(9, sum(strokes_one[:9]))
        strokes_two.insert(9, sum(strokes_two[:9]))
        # Total scores for both golfers
        scores_one += ['NA', 'NA']
        scores_two += ['NA', 'NA']
        scores_one.insert(9, 'NA')
        scores_two.insert(9, 'NA')
        zipped_scores_one = zip(strokes_one, scores_one)
        zipped_scores_two = zip(strokes_two, scores_two)
        scorecard = {'round': round, 'course': course, 'yardages': yardages,
                     'handicaps': handicaps, 'pars': pars,
                     'strokes_one': strokes_one, 'strokes_two': strokes_two,
                     'to_pars_one': to_pars_one, 'to_pars_two': to_pars_two,
                     'zipped_scores_one': zipped_scores_one,
                     'zipped_scores_two': zipped_scores_two,
                     }
        scorecards.append(scorecard)
    return scorecards


def get_course_avg_scorecard(rounds) -> list:
    """Returns a scorecard for averages on each hole of a course"""
    # Create a list for each row on the scorecard
    handicaps = []
    pars = []
    hole_scores = []
    yardages = []
    course = rounds[0].course
    hole_sum = [0] * 18  # Track strokes on each hole to calc the average
    holes = Hole.objects.filter(course=course).order_by(
        'tee')  # Get course holes
    # Update each row of the scorecard based on course holes
    for i in range(len(holes)):
        yardages.append(holes[i].yardage)
        handicaps.append(holes[i].handicap)
        pars.append(holes[i].par)
    # Calculate the total strokes on each hole
    for this_round in rounds:
        scores = Score.objects.filter(round=this_round)
        for i in range(len(scores)):
            hole_sum[i] += scores[i].score
    strokes = []  # Average strokes
    # Calculate average strokes
    for i in range(len(hole_sum)):
        hole_avg = round(hole_sum[i] / len(rounds), 1)
        strokes.append(hole_avg)
    # Get to pars based on average strokes
    to_pars = get_to_pars(strokes, pars)
    # Calculate scores for each hole
    for i in range(len(strokes)):
        this_score = round(strokes[i] - pars[i])
        hole_scores.append(this_score)
    # Total strokes
    strokes.append(round(sum(strokes[9:]), 1))
    strokes.append(round(sum(strokes[:-1]), 1))
    strokes.insert(9, round(sum(strokes[:9]), 1))
    # Total hole scores
    hole_scores += ['NA', 'NA']
    hole_scores.insert(9, 'NA')
    zipped_scores = zip(strokes, hole_scores)
    scorecard = {'course': course, 'yardages': yardages,
                 'handicaps': handicaps, 'pars': pars, 'strokes': strokes,
                 'to_pars': to_pars, 'zipped_scores': zipped_scores}
    return scorecard


def get_to_pars(strokes: list, pars: list) -> list:
    """Returns a list of relations to par based on a round"""
    to_pars = []
    # Track front-nine
    par_tracker = 0
    for i in range(9):
        to_this_par = strokes[i] - pars[i]
        if to_this_par == 0:
            to_pars.append(par_shift(round(par_tracker)))
        else:
            par_tracker += to_this_par
            to_pars.append(par_shift(round(par_tracker)))
    # Track back-nine
    par_tracker = 0
    for i in range(9):
        to_this_par = strokes[i + 9] - pars[i + 9]
        if to_this_par == 0:
            to_pars.append(par_shift(round(par_tracker)))
        else:
            par_tracker += to_this_par
            to_pars.append(par_shift(round(par_tracker)))
    # Total to_pars
    front_nine_to_par = par_shift(round(sum(strokes[:9]) - sum(pars[:9])))
    back_nine_to_par = par_shift(round(sum(strokes[9:]) - sum(pars[9:])))
    total_to_par = par_shift(round(sum(strokes) - sum(pars)))
    to_pars.append(back_nine_to_par)
    to_pars.append(total_to_par)
    to_pars.insert(9, front_nine_to_par)
    return to_pars


def api_add_course(request, pars: list, yardages: list, handicaps: list, new=True):
    """Adds a course to the database via API"""
    # Check if the course is new or just new tee's
    if new:
        tees = request.data['tee']
        course_name = request.data['newCourseName']
    else:
        tees = request.data['tee']
        course_name = request.data['course']
    course_abbreviation = abbreviate_course(course_name)
    yardages = request.data['yardages']
    yardages_front = sum(yardages[:9])
    yardages_back = sum(yardages[9:])
    yaradage_total = sum(yardages)
    pars = request.data['pars']
    pars_front = sum(pars[:9])
    pars_back = sum(pars[9:])
    pars_total = sum(pars)
    # Create Course
    this_course = Course(name=course_name,
                         tees=tees,
                         front_par=int(pars_front),
                         back_par=int(pars_back),
                         par=int(pars_total),
                         front_yardage=int(yardages_front),
                         back_yardage=int(yardages_back),
                         yardage=int(yaradage_total),
                         slope=int(request.data['slope']),
                         course_rating=float(request.data['courseRating']),
                         abbreviation=course_abbreviation)
    this_course.save()
    # Add holes
    for i in range(18):
        this_hole = Hole(course=this_course, tee=i+1,
                         par=pars[i], yardage=yardages[i],
                         handicap=handicaps[i])
        this_hole.save()


def add_course(request, pars: list, yardages: list, handicaps: list, new=True):
    """Adds a course to the database"""
    # Check if the course is new or just new tee's
    if new:
        tees = request.POST['new-tees']
        course_name = request.POST['new-course-name']
    else:
        tees = request.POST['tees-course-exists']
        course_name = request.POST['course-exists']
    course_abbreviation = abbreviate_course(course_name)
    yardages_front = request.POST['yardages-front']
    yardages_back = request.POST['yardages-back']
    # Create course
    this_course = Course(name=course_name,
                         tees=tees,
                         front_par=int(request.POST['par-front']),
                         back_par=int(request.POST['par-back']),
                         par=int(request.POST['par-total']),
                         front_yardage=int(yardages_front),
                         back_yardage=int(yardages_back),
                         yardage=int(request.POST['yardages-total']),
                         slope=int(request.POST['slope']),
                         course_rating=float(request.POST['rating']),
                         abbreviation=course_abbreviation)
    this_course.save()  # Save course
    # Add holes
    for i in range(18):
        this_hole = Hole(course=this_course, tee=i+1,
                         par=pars[i], yardage=yardages[i],
                         handicap=handicaps[i])
        this_hole.save()


def delete_rounds(rounds):
    """Deletes golfer rounds from the database"""
    for this_round in rounds:
        this_round.delete()
    return True


def post_match(request) -> tuple:
    """Validates input and posts a match"""
    # Ensure user is logged in
    if not request.user.is_authenticated:
        message = 'You must be logged in to post a match.'
        return (False, message)
    else:
        # Determine golfer count
        try:
            golfer_count = int(request.POST['number-of-golfers'])
        except:
            message = 'There was an error processing your request.'
            return (False, message)
        if golfer_count > 4 or golfer_count < 1:
            message = 'There was an error processing your request.'
            return (False, message)
        golfer_scores = []
        # Parse all the scores
        for i in range(golfer_count):
            golfer_score = []
            golfer = request.POST[f'golfer-{i + 1}']
            if golfer == 'Golfer':
                message = 'A golfer name was not selected.'
                return (False, message)
            golfer_score.append(golfer)
            for i in range(21):
                # Ensure user submitted a valid integer
                try:
                    this_score = int(request.POST[f'{golfer}-{i + 1}'])
                except:
                    message = 'All scores entered should be single numbers.'
                    return (False, message)
                golfer_score.append(this_score)
            # Ensure front nine adds up
            if sum(golfer_score[1:10]) != golfer_score[10]:
                message = f"{golfer}'s front nine scores do not add up."
                return (False, message)
            # Ensure back nine adds up
            elif sum(golfer_score[11:20]) != golfer_score[20]:
                message = f"{golfer}'s back nine scores do not add up."
                return (False, message)
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
                        return (False, message)
        # Store round information
        # Create new match_id
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
            this_round = Round(golfer=golfer, course=course,
                               date=date, match=match)
            this_round.save()
            # Add golfer to those who have rounds played
            golfer.has_rounds = True
            golfer.save()
            # Store each score
            for j in range(1, len(golfer_scores[i])):
                score = int(golfer_scores[i][j])
                hole = Hole.objects.get(course=course, tee=j)
                this_score = Score(
                    score=score, golfer=golfer, round=this_round, hole=hole)
                this_score.save()
        return (True, "Success")


def get_course_names(course: str) -> list:
    """Returns all unique course names"""
    courses = Course.objects.all().order_by('name')
    course_names = []
    for this_course in courses:
        if this_course.name not in course_names:
            course_names.append(this_course.name)
    # Move the selected course to the front of the list
    selected_course_index = course_names.index(course)
    if selected_course_index != 0:
        course_names.insert(0, course_names.pop(selected_course_index))
    return course_names


def get_tee_options(course: str, tees: str) -> list:
    """Returns all available tee options for a given course name"""
    tee_options = []
    duplicate_courses = Course.objects.filter(name=course)
    for course in duplicate_courses:
        tee_options.append(course.tees)
    if tees not in tee_options:
        return tee_options
    # Move selected tees to the front
    else:
        selected_tee_index = tee_options.index(tees)
        if selected_tee_index != 0:
            tee_options.insert(0, tee_options.pop(selected_tee_index))
        return tee_options


def get_course_info(course) -> list:
    """Returns scorecard information for a given course"""
    holes = Hole.objects.filter(course=course)
    yardages = []
    handicaps = []
    pars = []
    for i in range(len(holes)):
        yardages.append(holes[i].yardage)
        handicaps.append(holes[i].handicap)
        pars.append(holes[i].par)
    course_info = [pars, handicaps, yardages]
    return course_info


def get_bart_birdies() -> int:
    """Returns how many days since Bart's last birdie"""
    bart = User.objects.get(pk=7)
    barts_most_recent_birdie = Score.objects.filter(
        golfer=bart, score=F('hole__par')-1).order_by(
            '-round__date')[0].round.date
    now = datetime.now().date()
    delta = now - barts_most_recent_birdie
    return delta.days
