from django.shortcuts import render

from django.core.handlers.wsgi import WSGIRequest

from app.models import RiotAccount, RiotSoloRank, RiotSummoner
from users.models import AppUser

tier_colors = {
    "Unranked": {"color": "#000000", "bg": "#FFFFFF"},
    "IRON": {"color": "#3D2E2C", "bg": "#AD9F9B"},
    "BRONZE": {"color": "#613D35", "bg": "#BFA097"},
    "SILVER": {"color": "#4F585F", "bg": "#DBE7F1"},
    "GOLD": {"color": "#84613A", "bg": "#FEECBF"},
    "PLATIUM": {"color": "#1F7282", "bg": "#ADEBEB"},
    "EMERALD": {"color": "#065E39", "bg": "#78E9C6"},
    "DIAMOND": {"color": "#3E74DC", "bg": "#E0E2FC"},
    "MASTER": {"color": "#8D4C9D", "bg": "#F2C5F2"},
    "GRANDMASTER": {"color": "#8D4C9D", "bg": "#F2C5F2"},
    "CHALLENGER": {"color": "#8D4C9D", "bg": "#F2C5F2"},
}


def profile(request: WSGIRequest):
    user: AppUser = request.user

    riot_account: RiotAccount | None = user.riot_account
    riot_summoner: RiotSummoner | None = user.riot_summoner

    if riot_summoner:
        riot_solo_rank: RiotSoloRank | None = riot_summoner.riot_solo_rank
    else:
        riot_solo_rank: RiotSoloRank | None = None

    return render(
        request,
        "users/profile.html",
        {
            "user": user,
            "riot_account": riot_account,
            "riot_summoner": riot_summoner,
            "riot_solo_rank": riot_solo_rank,
            "tier_color": (
                tier_colors[riot_solo_rank.tier]
                if riot_solo_rank and riot_solo_rank.tier in tier_colors
                else tier_colors["Unranked"]
            ),
        },
    )
