# Generated by Django 2.0.7 on 2018-08-07 20:55

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import model_utils.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('ej_candidates', '0005_delete_candidate'),
    ]

    operations = [
        migrations.CreateModel(
            name='Candidate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='The name of the candidate', max_length=100)),
                ('candidacy', model_utils.fields.StatusField(choices=[('senadora', 'senadora')], default='senadora', help_text='the candadite candidacy', max_length=100, no_check_for_status=True)),
                ('urn', models.IntegerField(help_text='The candidate urn number')),
                ('party', model_utils.fields.StatusField(choices=[('pt', 'pt'), ('psdb', 'psdb')], default='pt', help_text='The candidate party initials', max_length=100, no_check_for_status=True)),
                ('image', models.FileField(default='default.jpg', upload_to='candidates')),
            ],
        ),
        migrations.CreateModel(
            name='SelectedCandidates',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('candidate', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='ej_candidates.Candidate')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
