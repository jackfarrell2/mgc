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
    par = models.IntegerField()
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