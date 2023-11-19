# Generated by Django 4.0.6 on 2022-08-26 17:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('golf', '0014_course_has_rounds'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='course',
            name='has_rounds',
        ),
        migrations.AddField(
            model_name='user',
            name='has_rounds',
            field=models.BooleanField(default=False),
        ),
    ]
