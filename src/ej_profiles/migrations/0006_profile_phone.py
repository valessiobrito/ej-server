# Generated by Django 2.0.6 on 2018-07-10 19:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ej_profiles', '0005_auto_20180704_1207'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='phone',
            field=models.CharField(blank=True, max_length=50, verbose_name='Phone'),
        ),
    ]