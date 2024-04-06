# Create your models here.

from datetime import datetime
import uuid
from users.models import AppUser as User
from django.db import models
from app.riot_client import get_client
import logging

logger = logging.getLogger(__name__)


class NoSoloRankException(Exception):
    pass


class UserActivity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    path = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.path}"


class Champion(models.Model):
    version = models.CharField(max_length=255)
    id = models.CharField(max_length=255, primary_key=True)
    key = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    blurb = models.TextField()
    info = models.JSONField()
    image = models.JSONField()
    tags = models.JSONField()
    partype = models.CharField(max_length=255)
    stats = models.JSONField()


class Summoner(models.Model):
    id = models.CharField(max_length=100, blank=False, null=False, primary_key=True)
    name = models.CharField(max_length=100, blank=False, null=False)
    puuid = models.CharField(max_length=100, blank=False, null=True)
    account_id = models.CharField(max_length=100, blank=False, null=True)
    profile_icon_id = models.IntegerField(blank=False, null=True)
    revision_date = models.BigIntegerField(blank=False, null=True)
    summoner_level = models.IntegerField(blank=False, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        indexes = [models.Index(fields=["name"])]


class LeagueEntry(models.Model):
    summoner = models.ForeignKey(Summoner, on_delete=models.CASCADE)
    tier = models.CharField(max_length=255)
    rank = models.CharField(max_length=255)
    league_points = models.IntegerField()
    wins = models.IntegerField()
    losses = models.IntegerField()
    veteran = models.BooleanField()
    inactive = models.BooleanField()
    fresh_blood = models.BooleanField()
    hot_streak = models.BooleanField()
    queue_type = models.CharField(max_length=255)
    league_id = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.summoner.name} - {self.tier} {self.rank}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["summoner", "queue_type"], name="unique_league_entry"
            )
        ]


class DuoMatch(models.Model):
    id = models.CharField(
        max_length=36, blank=False, null=False, primary_key=True, default=uuid.uuid4
    )
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user1")
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user2")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user1.username} - {self.user2.username}"


class DuoMatchFeedback(models.Model):
    duo_match = models.ForeignKey(DuoMatch, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.rating}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["duo_match", "user"], name="unique_duo_match_feedback"
            )
        ]


class DuoMatchReport(models.Model):
    duo_match = models.ForeignKey(DuoMatch, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.reason}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["duo_match", "user"], name="unique_duo_match_report"
            )
        ]


class RiotAccount(models.Model):
    puuid = models.CharField(max_length=100, blank=False, null=False, primary_key=True)
    game_name = models.CharField(max_length=100, blank=False, null=False)
    tag_line = models.CharField(max_length=100, blank=False, null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.game_name}#{self.tag_line}"

    def refresh(self, access_token):
        client = get_client()

        if not access_token:
            raise Exception("No access token")

        response = client.get_accounts_me(access_token)

        if response.status_code == 401:
            riot_token = RiotToken.objects.get(access_token=access_token)
            riot_token.refresh()

        if response.status_code != 200:
            raise Exception("Failed to refresh account")

        data = response.json()
        self.game_name = data["gameName"]
        self.tag_line = data["tagLine"]
        self.save()

        return True

    @classmethod
    def create(cls, access_token) -> "RiotAccount":
        client = get_client()

        response = client.get_accounts_me(access_token)

        if response.status_code == 401:
            riot_token = RiotToken.objects.get(access_token=access_token)
            riot_token.refresh()

        if response.status_code != 200:
            raise Exception("Failed to create account")

        data = response.json()

        if RiotAccount.objects.filter(puuid=data["puuid"]).exists():
            riot_account = RiotAccount.objects.get(puuid=data["puuid"])
            riot_account.game_name = data["gameName"]
            riot_account.tag_line = data["tagLine"]

            return riot_account

        return RiotAccount.objects.create(
            puuid=data["puuid"],
            game_name=data["gameName"],
            tag_line=data["tagLine"],
        )


class RiotToken(models.Model):
    id_token = models.CharField(max_length=1024, primary_key=True)
    access_token = models.CharField(max_length=1024)
    token_type = models.CharField(max_length=255)
    expires_in = models.IntegerField()
    refresh_token = models.CharField(max_length=1024)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.access_token

    def is_expired(self):
        return (
            self.updated_at.timestamp() + self.expires_in < datetime.now().timestamp()
        )

    def refresh(self):
        if not self.is_expired():
            return False

        client = get_client()

        response = client.refresh_token(self.refresh_token)

        if response.status_code != 200:
            raise Exception("Failed to refresh token")

        data = response.json()
        self.access_token = data["access_token"]
        self.token_type = data["token_type"]
        self.expires_in = data["expires_in"]
        self.refresh_token = data["refresh_token"]
        self.id_token = data["id_token"]
        self.save()

        return True

    @classmethod
    def create(cls, code: str, redirect_uri: str) -> "RiotToken":
        client = get_client()

        response = client.get_token(redirect_uri, code)

        if response.status_code != 200:
            raise Exception("Failed to get token")

        data = response.json()

        if RiotToken.objects.filter(id_token=data["id_token"]).exists():
            riot_token = RiotToken.objects.get(id_token=data["id_token"])
            riot_token.access_token = data["access_token"]
            riot_token.token_type = data["token_type"]
            riot_token.expires_in = data["expires_in"]
            riot_token.refresh_token = data["refresh_token"]

            return riot_token

        return RiotToken.objects.create(
            id_token=data["id_token"],
            access_token=data["access_token"],
            token_type=data["token_type"],
            expires_in=data["expires_in"],
            refresh_token=data["refresh_token"],
        )


class RiotSummoner(models.Model):
    id = models.CharField(max_length=100, blank=False, null=False, primary_key=True)
    riot_solo_rank = models.OneToOneField(
        "RiotSoloRank", on_delete=models.CASCADE, blank=True, null=True
    )
    puuid = models.CharField(max_length=100, blank=False, null=False)
    account_id = models.CharField(max_length=100, blank=False, null=False)
    name = models.CharField(max_length=100, blank=False, null=False)
    profile_icon_id = models.IntegerField(blank=False, null=False)
    revision_date = models.BigIntegerField(blank=False, null=False)
    summoner_level = models.IntegerField(blank=False, null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def refresh(self, access_token):
        client = get_client()

        response = client.get_summoners_me(access_token)

        if response.status_code == 401:
            riot_token = RiotToken.objects.get(access_token=access_token)
            riot_token.refresh()

        if response.status_code != 200:
            raise Exception("Failed to refresh account")

        data = response.json()
        self.id = data["id"]
        self.puuid = data["puuid"]
        self.account_id = data["accountId"]
        self.name = data["name"]
        self.profile_icon_id = data["profileIconId"]
        self.revision_date = data["revisionDate"]
        self.summoner_level = data["summonerLevel"]
        self.save()

        return True

    @classmethod
    def create(cls, access_token) -> "RiotSummoner":
        client = get_client()

        response = client.get_summoners_me(access_token)

        if response.status_code == 401:
            riot_token = RiotToken.objects.get(access_token=access_token)
            riot_token.refresh()

        if response.status_code != 200:
            raise Exception("Failed to create account")

        data = response.json()

        if RiotSummoner.objects.filter(id=data["id"]).exists():
            riot_summoner = RiotSummoner.objects.get(id=data["id"])
            riot_summoner.puuid = data["puuid"]
            riot_summoner.account_id = data["accountId"]
            riot_summoner.name = data["name"]
            riot_summoner.profile_icon_id = data["profileIconId"]
            riot_summoner.revision_date = data["revisionDate"]
            riot_summoner.summoner_level = data["summonerLevel"]

            return riot_summoner

        return RiotSummoner.objects.create(
            id=data["id"],
            puuid=data["puuid"],
            account_id=data["accountId"],
            name=data["name"],
            profile_icon_id=data["profileIconId"],
            revision_date=data["revisionDate"],
            summoner_level=data["summonerLevel"],
        )


class RiotSoloRank(models.Model):
    riot_summoner = models.OneToOneField("RiotSummoner", on_delete=models.CASCADE)
    league_id = models.CharField(max_length=255, blank=False, null=False)
    queue_type = models.CharField(max_length=255, blank=False, null=False)
    tier = models.CharField(max_length=255, blank=False, null=False)
    rank = models.CharField(max_length=255, blank=False, null=False)
    league_points = models.IntegerField(blank=False, null=False)
    wins = models.IntegerField(blank=False, null=False)
    losses = models.IntegerField(blank=False, null=False)
    veteran = models.BooleanField(blank=False, null=False)
    inactive = models.BooleanField(blank=False, null=False)
    fresh_blood = models.BooleanField(blank=False, null=False)
    hot_streak = models.BooleanField(blank=False, null=False)

    def __str__(self):
        return f"{self.riot_summoner.name} - {self.tier} {self.rank}"

    def refresh(self):
        client = get_client()

        response = client.get_league_entries_by_summoner_id(self.riot_summoner.id)

        if response.status_code != 200:
            raise Exception("Failed to refresh account")

        data = response.json()
        solo_rank = None
        for entry in data:
            if entry["queueType"] == "RANKED_SOLO_5x5":
                solo_rank = entry
                break

        if solo_rank is None:
            raise Exception("No solo rank")

        self.league_id = solo_rank["leagueId"]
        self.queue_type = solo_rank["queueType"]
        self.tier = solo_rank["tier"]
        self.rank = solo_rank["rank"]
        self.league_points = solo_rank["leaguePoints"]
        self.wins = solo_rank["wins"]
        self.losses = solo_rank["losses"]
        self.veteran = solo_rank["veteran"]
        self.inactive = solo_rank["inactive"]
        self.fresh_blood = solo_rank["freshBlood"]
        self.hot_streak = solo_rank["hotStreak"]
        self.save()

        return True

    @classmethod
    def create(cls, summoner_id) -> "RiotSoloRank":
        if RiotSoloRank.objects.filter(riot_summoner_id=summoner_id).exists():
            return RiotSoloRank.objects.get(riot_summoner_id=summoner_id)

        client = get_client()

        response = client.get_league_entries_by_summoner_id(summoner_id)

        if response.status_code != 200:
            logger.error(response.json())
            raise Exception("Failed to refresh account")

        data = response.json()
        solo_rank = None
        for entry in data:
            if entry["queueType"] == "RANKED_SOLO_5x5":
                solo_rank = entry
                break

        if solo_rank is None:
            raise NoSoloRankException("No solo rank")

        return RiotSoloRank.objects.create(
            riot_summoner_id=summoner_id,
            league_id=solo_rank["leagueId"],
            queue_type=solo_rank["queueType"],
            tier=solo_rank["tier"],
            rank=solo_rank["rank"],
            league_points=solo_rank["leaguePoints"],
            wins=solo_rank["wins"],
            losses=solo_rank["losses"],
            veteran=solo_rank["veteran"],
            inactive=solo_rank["inactive"],
            fresh_blood=solo_rank["freshBlood"],
            hot_streak=solo_rank["hotStreak"],
        )
