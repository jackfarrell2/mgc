# Generated by Django 4.0.6 on 2022-08-17 22:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('golf', '0009_course_course_rating_course_slope'),
    ]

    operations = [
        migrations.AlterField(
            model_name='course',
            name='course_rating',
            field=models.DecimalField(decimal_places=2, max_digits=3),
        ),
    ]