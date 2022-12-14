from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Golfer and Site User"""
    has_rounds = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.first_name}"


class Course(models.Model):
    """Golf Course - Specific to tee"""
    name = models.CharField(max_length=50)
    WHITE = 'White'
    BLUE = 'Blue'
    RED = 'Red'
    BLACK = 'Black'
    TEE_CHOICES = [
        (WHITE, 'White'),
        (BLUE, 'Blue'),
        (RED, 'Red'),
        (BLACK, 'Black')
    ]
    tees = models.CharField(max_length=6, choices=TEE_CHOICES, default=WHITE)
    course_rating = models.DecimalField(max_digits=3, decimal_places=1)
    slope = models.IntegerField()
    front_par = models.IntegerField()
    back_par = models.IntegerField()
    par = models.IntegerField()
    front_yardage = models.IntegerField()
    back_yardage = models.IntegerField()
    yardage = models.IntegerField()
    abbreviation = models.CharField(max_length=10)

    def __str__(self):
        return f"{self.name}"


class Round(models.Model):
    """Golfers round information"""
    golfer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="users_rounds")
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    date = models.DateField()
    match = models.IntegerField(default=0)
    solo_round = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.golfer} - {self.course} - {self.match} - {self.date}"


class Hole(models.Model):
    """Every hole for each course"""
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    tee = models.IntegerField()
    par = models.IntegerField()
    yardage = models.IntegerField()
    handicap = models.IntegerField()

    def __str__(self):
        return f"{self.tee} - {self.course}"


class Score(models.Model):
    """Golfers score on a single hole"""
    score = models.IntegerField()
    golfer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="golfers_scores")
    round = models.ForeignKey(
        Round, on_delete=models.CASCADE, related_name="round_scores")
    hole = models.ForeignKey(
        Hole, on_delete=models.CASCADE, related_name="holes_scores")

    def __str__(self):
        return f"{self.golfer}: {self.score} - {self.hole}"
