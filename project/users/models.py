from django.contrib.auth.models import AbstractUser
from django.db import models


class AppUser(AbstractUser):

    summoner = models.OneToOneField(
        "app.Summoner", on_delete=models.CASCADE, blank=True, null=True
    )

    riot_summoner = models.ForeignKey(
        "app.RiotSummoner", on_delete=models.CASCADE, blank=True, null=True
    )

    riot_account = models.ForeignKey(
        "app.RiotAccount", on_delete=models.CASCADE, blank=True, null=True
    )

    riot_token = models.ForeignKey(
        "app.RiotToken", on_delete=models.CASCADE, blank=True, null=True
    )
