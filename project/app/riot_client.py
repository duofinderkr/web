import requests

from project.config import get_config
from requests.auth import HTTPBasicAuth


KR_API_HOST = "https://kr.api.riotgames.com"
ASIA_API_HOST = "https://asia.api.riotgames.com"
AUTH_HOST = "https://auth.riotgames.com"


class RiotClient:
    def __init__(self):
        self.api_key = get_config().riot.api_key

    def get_account_by_summoner_name(self, summoner_name) -> requests.Response:
        url = f"{KR_API_HOST}/lol/summoner/v4/summoners/by-name/{summoner_name}"
        response = requests.get(url, headers={"X-Riot-Token": self.api_key})
        return response

    def get_match_list(self, puuid: str) -> requests.Response:
        url = f"{ASIA_API_HOST}/lol/match/v5/matches/by-puuid/{puuid}/ids"
        response = requests.get(url, headers={"X-Riot-Token": self.api_key})
        return response

    def get_match(self, match_id: str) -> requests.Response:
        url = f"{ASIA_API_HOST}/lol/match/v5/matches/{match_id}"
        response = requests.get(url, headers={"X-Riot-Token": self.api_key})
        return response

    def get_champion_masteries_by_puuid_top(self, puuid: str) -> requests.Response:
        url = f"{KR_API_HOST}/lol/champion-mastery/v4/champion-masteries/by-puuid/{puuid}/top"
        response = requests.get(url, headers={"X-Riot-Token": self.api_key})
        return response

    def get_summoner_by_encrypted_summoner_id(
        self, encrypted_summoner_id: str
    ) -> requests.Response:
        url = f"{KR_API_HOST}/lol/summoner/v4/summoners/{encrypted_summoner_id}"
        response = requests.get(url, headers={"X-Riot-Token": self.api_key})
        return response

    def get_token(
        self,
        redirect_uri: str,
        code: str,
    ) -> requests.Response:
        config = get_config()

        return requests.post(
            f"{AUTH_HOST}/token",
            auth=HTTPBasicAuth(
                config.riot.rso_client_id,
                config.riot.rso_client_secret,
            ),
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
            },
        )

    def refresh_token(
        self,
        refresh_token: str,
    ) -> requests.Response:
        config = get_config()

        return requests.post(
            f"{AUTH_HOST}/token",
            auth=HTTPBasicAuth(
                config.riot.rso_client_id,
                config.riot.rso_client_secret,
            ),
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            },
        )

    def get_userinfo(
        self,
        access_token: str,
    ) -> requests.Response:
        return requests.get(
            f"{AUTH_HOST}/userinfo",
            headers={
                "Authorization": f"Bearer {access_token}",
            },
        )

    def get_accounts_me(
        self,
        access_token: str,
    ) -> requests.Response:
        return requests.get(
            f"{ASIA_API_HOST}/riot/account/v1/accounts/me",
            headers={
                "Authorization": f"Bearer {access_token}",
            },
        )

    def get_summoners_me(
        self,
        access_token: str,
    ) -> requests.Response:
        return requests.get(
            f"{KR_API_HOST}/lol/summoner/v4/summoners/me",
            headers={
                "Authorization": f"Bearer {access_token}",
            },
        )

    def get_league_entries_by_summoner_id(
        self,
        summoner_id: str,
    ) -> requests.Response:
        return requests.get(
            f"{KR_API_HOST}/lol/league/v4/entries/by-summoner/{summoner_id}",
            headers={
                "X-Riot-Token": self.api_key,
            },
        )


client = RiotClient()


def get_client():
    return client
