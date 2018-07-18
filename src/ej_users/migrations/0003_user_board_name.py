# Generated by Django 2.0.6 on 2018-07-18 12:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ej_users', '0002_auto_20180529_0043'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='board_name',
            field=models.CharField(help_text='The name of the conversation board of an user.', max_length=140, null=True, unique=True, verbose_name='Board name'),
        ),
    ]