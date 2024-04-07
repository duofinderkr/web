import requests

from project.config import get_config
from requests.auth import HTTPBasicAuth


KR_API_HOST = "https://kr.api.riotgames.com"
ASIA_API_HOST = "https://asia.api.riotgames.com"
AUTH_HOST = "https://auth.riotgames.com"


class RiotClient:
    def __init__(self):
        self.api_key = get_config().riot.api_key

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
