# Generated by Django 5.0.2 on 2024-03-18 06:20

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0007_summoner_account_id_summoner_profile_icon_id_and_more"),
        ("users", "0002_summonerinfo_remove_appuser_riot_id_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="appuser",
            name="summoner_info",
        ),
        migrations.AddField(
            model_name="appuser",
            name="summoner",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="app.summoner",
            ),
        ),
        migrations.DeleteModel(
            name="SummonerInfo",
        ),
    ]
