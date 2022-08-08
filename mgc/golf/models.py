from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    def __str__(self):
        return f"{self.first_name}"

class Course(models.Model):
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
    front_par = models.IntegerField()
    back_par = models.IntegerField()
    par = models.IntegerField()
    front_yardage = models.IntegerField()
    back_yardage = models.IntegerField()
    yardage = models.IntegerField()

    def __str__(self):
        return f"{self.name} - {self.tees}"

class Round(models.Model):
    golfer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="users_rounds")
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    date = models.DateField()

    def __str__(self):
        return f"{self.golfer} - {self.course} - {self.date}"

class Hole(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    tee = models.IntegerField()
    par = models.IntegerField()
    yardage = models.IntegerField()
    handicap = models.IntegerField()

    def __str__(self):
        return f"{self.tee} - {self.course}"

class Score(models.Model):
    score = models.IntegerField()
    golfer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="golfers_scores")
    round = models.ForeignKey(Round, on_delete=models.CASCADE, related_name="round_scores")
    hole = models.ForeignKey(Hole, on_delete=models.CASCADE, related_name="holes_scores")

    def __str__(self):
        return f"{self.score} - {self.hole}"