from django.contrib import admin
from .models import User, Round, Course, Hole, Score

# Register your models here.
admin.site.register(User)
admin.site.register(Round)
admin.site.register(Course)
admin.site.register(Hole)
admin.site.register(Score)
