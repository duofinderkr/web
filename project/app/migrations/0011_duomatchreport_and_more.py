# Generated by Django 5.0.2 on 2024-04-06 16:47

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0010_duomatch_updated_at_duomatchfeedback"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="DuoMatchReport",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("reason", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.AddConstraint(
            model_name="duomatchfeedback",
            constraint=models.UniqueConstraint(
                fields=("duo_match", "user"), name="unique_duo_match_feedback"
            ),
        ),
        migrations.AddField(
            model_name="duomatchreport",
            name="duo_match",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="app.duomatch"
            ),
        ),
        migrations.AddField(
            model_name="duomatchreport",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddConstraint(
            model_name="duomatchreport",
            constraint=models.UniqueConstraint(
                fields=("duo_match", "user"), name="unique_duo_match_report"
            ),
        ),
    ]