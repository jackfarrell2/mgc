# Generated by Django 4.0.6 on 2022-08-04 01:24

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('golf', '0003_rename_number_hole_tee_course_par_course_yardage'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='name',
        ),
    ]
