import datetime
from urllib.parse import urlencode
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.core.handlers.wsgi import WSGIRequest
from django.contrib.auth.decorators import login_required
from django.db import transaction
from uuid import uuid4
from allauth.socialaccount.models import SocialAccount, EmailAddress

from app.models import (
    DuoMatch,
    DuoMatchFeedback,
    DuoMatchReport,
    NoSoloRankException,
    RiotAccount,
    RiotSoloRank,
    RiotSummoner,
    RiotToken,
    Summoner,
)
from rest_framework.decorators import api_view
from app.riot_client import get_client
from app.serializers import SummonerSerializer, LeagueEntrySerializer
from app.models import LeagueEntry
from project.config import get_config
from users.models import AppUser

import logging

logger = logging.getLogger(__name__)

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


def riot_txt(request: WSGIRequest):
    return render(request, "riot.txt")


def index(request: WSGIRequest):
    return render(
        request,
        "index.html",
        {"user": request.user, "login_url": "http://localhost:8000/accounts/login"},
    )


def authorize(request: WSGIRequest):
    provider = "https://auth.riotgames.com"

    redirect_uri = "http://localhost:8000/oauth2-callback"
    client_id = ""
    response_type = "code"
    scope = "openid"

    url = f"{provider}/authorize?client_id={client_id}&redirect_uri={redirect_uri}&response_type={response_type}&scope={scope}"

    return redirect(url)


def get_account_by_summoner_name(request: WSGIRequest):
    summoner_name = request.GET.get("summoner_name")
    if Summoner.objects.filter(name=summoner_name).exists():
        summoner = Summoner.objects.get(name=summoner_name)

        return render(request, "summoner/index.html", {"summoner": summoner})

    client = get_client()

    response = client.get_account_by_summoner_name(summoner_name)

    if response.status_code == 200:
        data = response.json()

        summoner = Summoner(
            id=data["id"],
            account_id=data["accountId"],
            profile_icon_id=data["profileIconId"],
            revision_date=data["revisionDate"],
            name=data["name"],
            puuid=data["puuid"],
            summoner_level=data["summonerLevel"],
        )

        summoner.save()

        return render(request, "summoner/index.html", {"summoner": summoner})

    return render(request, "summoner/index.html", {"error": response.json()})


def recommend_ai(request: WSGIRequest):
    user: AppUser = request.user

    return render(
        request,
        "recommend/ai.html",
        {
            "user": user,
            "riot_account": user.riot_account,
            "riot_summoner": user.riot_summoner,
        },
    )


@login_required
def recommend_result(request: WSGIRequest):
    return render(
        request,
        "recommend/result.html",
        {"user": request.user},
    )


@api_view(["GET"])
def search_summoners_by_name(request: WSGIRequest):
    name = request.GET.get("name")
    count = request.GET.get("count")
    if not name or not count:
        return JsonResponse({"error": "name, count are required"}, status=400)

    try:
        count = int(count)
    except ValueError:
        return JsonResponse({"error": "count must be an integer"}, status=400)

    if count > 10:
        return JsonResponse(
            {"error": "count must be less than or equal to 10"}, status=400
        )

    queryset = Summoner.objects.filter(name__startswith=name)[:count]
    serializer = SummonerSerializer(queryset, many=True)

    summoners = serializer.data

    summoner_ids = [summoner["id"] for summoner in serializer.data]

    queryset = LeagueEntry.objects.filter(summoner_id__in=summoner_ids)
    serializer = LeagueEntrySerializer(queryset, many=True)

    league_entries = serializer.data

    for summoner in summoners:
        if summoner["puuid"] is None:
            new_summoner = get_client().get_summoner_by_encrypted_summoner_id(
                summoner["id"]
            )

            if new_summoner.status_code == 200:
                summoner["puuid"] = new_summoner.json()["puuid"]
                summoner["account_id"] = new_summoner.json()["accountId"]
                summoner["profile_icon_id"] = new_summoner.json()["profileIconId"]
                summoner["revision_date"] = new_summoner.json()["revisionDate"]
                summoner["summoner_level"] = new_summoner.json()["summonerLevel"]

                Summoner.objects.filter(id=summoner["id"]).update(
                    puuid=summoner["puuid"],
                    account_id=summoner["account_id"],
                    profile_icon_id=summoner["profile_icon_id"],
                    revision_date=summoner["revision_date"],
                    summoner_level=summoner["summoner_level"],
                )

    result = [
        {
            "summoner": summoner,
            "league_entries": [
                league_entry
                for league_entry in league_entries
                if league_entry["summoner"] == summoner["id"]
            ],
        }
        for summoner in summoners
    ]

    return JsonResponse(result, safe=False)


@api_view(["POST"])
def save_summoner(request: WSGIRequest):
    me = request.user

    summoner_id = request.data["summoner_id"]

    if not summoner_id:
        return JsonResponse({"error": "id is required"}, status=400)

    summoner = Summoner.objects.get(id=summoner_id)

    AppUser.objects.filter(id=me.id).update(summoner=summoner)

    return JsonResponse(
        {
            "name": summoner.name,
            "puuid": summoner.puuid,
            "level": summoner.summoner_level,
            "account_id": summoner.account_id,
            "profile_icon_id": summoner.profile_icon_id,
            "revision_date": summoner.revision_date,
        },
        safe=False,
    )


def terms_of_service(request: WSGIRequest):
    return render(request, "terms_of_service.html")


def privacy_policy(request: WSGIRequest):
    return render(request, "privacy_policy.html")


def riot_sign_on(request: WSGIRequest):
    url = "https://auth.riotgames.com/authorize?"

    query_string = urlencode(
        {
            "client_id": get_config().riot.rso_client_id,
            "redirect_uri": "https://" + request.get_host() + "/accounts/riot/callback",
            "response_type": "code",
            "scope": "openid",
        }
    )

    return redirect(url + query_string)


@transaction.atomic
def riot_sign_on_callback(request: WSGIRequest):
    user: AppUser = request.user

    code = request.GET.get("code")

    if not code:
        return JsonResponse({"error": "code is required"}, status=400)

    riot_token: RiotToken = RiotToken.create(
        code=code,
        redirect_uri="https://" + request.get_host() + "/accounts/riot/callback",
    )

    riot_account = RiotAccount.create(riot_token.access_token)

    riot_summoner: RiotSummoner = RiotSummoner.create(riot_token.access_token)

    user.riot_token = riot_token
    user.riot_account = riot_account
    user.riot_summoner = riot_summoner
    user.save()

    try:
        riot_solo_rank = RiotSoloRank.create(riot_summoner.id)

        riot_summoner.riot_solo_rank = riot_solo_rank
        riot_summoner.save()
    except NoSoloRankException:
        pass
    except Exception as e:
        logger.error(e)
        return render(
            request,
            "users/profile.html",
            {
                "user": request.user,
                "error": "계정 연동에 실패했습니다.",
            },
        )

    return redirect("users:profile")


@api_view(["POST"])
@transaction.atomic
def riot_account_refresh(request: WSGIRequest):
    user: AppUser = request.user

    try:
        token: RiotToken = user.riot_token
        token.refresh()
    except Exception as e:
        logger.error(e)
        return JsonResponse({"error": "전적 갱신에 실패했습니다."}, status=400)

    try:
        account: RiotAccount = user.riot_account
        if account.updated_at + datetime.timedelta(minutes=3) > datetime.datetime.now(
            datetime.timezone.utc
        ):
            return JsonResponse(
                {
                    "error": f"전적 갱신은 3분에 한 번만 가능합니다. 남은 시간: {180 - (datetime.datetime.now(datetime.timezone.utc) - account.updated_at).seconds}초"
                },
                status=400,
            )
        account.refresh(token.access_token)
    except Exception as e:
        logger.error(e)
        return JsonResponse({"error": "전적 갱신에 실패했습니다."}, status=400)

    try:
        summoner: RiotSummoner = user.riot_summoner
        summoner.refresh(token.access_token)
    except Exception as e:
        logger.error(e)
        return JsonResponse({"error": "전적 갱신에 실패했습니다."}, status=400)

    if RiotSoloRank.objects.filter(riot_summoner=summoner).count() == 0:
        try:
            RiotSoloRank.create(summoner.id)
        except NoSoloRankException:
            pass
    else:
        summoner.riot_solo_rank.refresh()

    return JsonResponse({"message": "전적 갱신에 성공했습니다."})


@api_view(["POST"])
def inference(request: WSGIRequest):
    me: AppUser = request.user

    rank_range = {
        "IRON": ["IRON", "BRONZE", "SILVER"],
        "BRONZE": ["IRON", "BRONZE", "SILVER"],
        "SILVER": ["BRONZE", "SILVER", "GOLD"],
        "GOLD": ["SILVER", "GOLD", "PLATINUM"],
        "PLATINUM": ["GOLD", "PLATINUM", "EMERALD"],
        "EMERALD": ["PLATINUM", "EMERALD", "DIAMOND"],
        "DIAMOND": ["EMERALD", "DIAMOND"],
    }

    my_rank = me.riot_summoner.riot_solo_rank.tier

    # 1. 나를 제외한 모든 유저 중에서 랭크가 있는 유저를 찾는다.
    # 2. 랭크가 있는 유저 중에서 랭크가 비슷한 유저를 찾는다.
    candidates = (
        AppUser.objects.filter(riot_summoner__isnull=False)
        .filter(riot_summoner__riot_solo_rank__isnull=False)
        .filter(riot_summoner__riot_solo_rank__tier__in=rank_range[my_rank])
        .exclude(id=me.id)
    )

    my_match_histories = [
        duo_match.user2 for duo_match in DuoMatch.objects.filter(user1=me)
    ]

    my_match_histories += [
        duo_match.user1 for duo_match in DuoMatch.objects.filter(user2=me)
    ]

    # 만약 이미 매칭된 유저가 있다면 그 유저는 제외한다.
    for candidate in candidates:
        for history in my_match_histories:
            if candidate == history:
                candidates = candidates.exclude(id=candidate.id)

    if candidates.count() == 0:
        return JsonResponse({"error": "현재 매칭할 유저가 없습니다."}, status=400)

    user = me

    result = DuoMatch.objects.create(user1=me, user2=user)
    result.save()

    return JsonResponse(
        {
            "duo_match_id": result.id,
            "user1": me.username,
            "user2": user.username,
        },
        safe=False,
    )


@api_view(["POST"])
def riot_account_disconnect(request: WSGIRequest):
    user: AppUser = request.user

    user.riot_summoner = None
    user.riot_account = None
    user.riot_token = None

    user.save()

    return JsonResponse({"message": "계정 연동 해제에 성공했습니다."})


def get_duo_match(request: WSGIRequest):
    duo_match_id = request.GET.get("duo_match_id")

    if not duo_match_id:
        return JsonResponse({"error": "duo_match_id is required"}, status=400)

    duo_match = DuoMatch.objects.get(id=duo_match_id)

    summoner2: RiotSummoner = duo_match.user2.riot_summoner

    summoner2_rank = RiotSoloRank.objects.get(riot_summoner=summoner2)

    summoner2_account = RiotAccount.objects.get(puuid=summoner2.puuid)

    my_duo_match_feedback = DuoMatchFeedback.objects.filter(
        duo_match=duo_match, user=request.user
    ).first()

    my_duo_match_report_exists = DuoMatchReport.objects.filter(
        duo_match=duo_match, user=request.user
    ).exists()

    return render(
        request,
        "recommend/duo_match.html",
        {
            "duo_match_id": duo_match_id,
            "user": request.user,
            "summoner1": duo_match.user1.riot_summoner,
            "summoner2": duo_match.user2.riot_summoner,
            "my_duo_match_feedback": my_duo_match_feedback,
            "my_duo_match_report_exists": my_duo_match_report_exists,
            "summoner2_rank": summoner2_rank,
            "summoner2_account": summoner2_account,
            "tier_color": tier_colors[summoner2_rank.tier],
        },
    )


def _n_days_ago(target_date: datetime.datetime):
    timezone = datetime.timezone(datetime.timedelta(hours=9))
    today = datetime.datetime.now().astimezone(timezone)

    diff = today - target_date.astimezone(timezone)

    if diff.days == 0 and diff.seconds < 3600:
        return f"{diff.seconds // 60}분 전"

    if diff.days == 0:
        return f"{diff.seconds // 3600}시간 전"

    if diff.days < 7:
        return f"{diff.days}일 전"

    return f"{diff.days}일 전"


@login_required(login_url="/accounts/discord/login/")
def get_duo_match_history(request: WSGIRequest):
    me = request.user
    timezone = datetime.timezone(datetime.timedelta(hours=9))

    duo_match_to_feedbacks = {
        duo_match_feedback.duo_match_id: duo_match_feedback
        for duo_match_feedback in DuoMatchFeedback.objects.filter(user=me)
    }

    duo_matches = [
        {
            "id": duo_match.id,
            "target_username": duo_match.user2.riot_summoner.name,
            "target_profile_icon_id": duo_match.user2.riot_summoner.profile_icon_id,
            "target_summoner_tier": duo_match.user2.riot_summoner.riot_solo_rank.tier,
            "target_summoner_rank": duo_match.user2.riot_summoner.riot_solo_rank.rank,
            "target_summoner_league_points": duo_match.user2.riot_summoner.riot_solo_rank.league_points,
            "created_at": duo_match.created_at.astimezone(timezone).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "n_days_ago": _n_days_ago(duo_match.created_at),
            "feedback": duo_match_to_feedbacks.get(duo_match.id, None),
            "tier_color": tier_colors[
                duo_match.user2.riot_summoner.riot_solo_rank.tier
            ],
        }
        for duo_match in DuoMatch.objects.filter(user1=me).order_by("-created_at")
    ]

    return render(
        request,
        "recommend/history.html",
        {"user": me, "duo_matches": duo_matches},
    )


@login_required
@transaction.atomic
def sign_out(request: WSGIRequest):
    user: AppUser = request.user

    delete_id = uuid4().hex

    user.riot_summoner = None
    user.riot_account = None
    user.riot_token = None
    user.email = delete_id + "@is-deleted-duofinder.kr"

    user.username = delete_id + "@is-deleted-duofinder.kr"

    SocialAccount.objects.filter(user=user).delete()
    EmailAddress.objects.filter(user=user).delete()

    user.is_active = False

    user.save()

    return redirect("home")


@login_required
@api_view(["POST"])
@transaction.atomic
def duo_match_feedback(request: WSGIRequest):
    me = request.user
    duo_match_id = request.data["duo_match_id"]
    feedback: str = request.data["feedback"]

    if feedback.lower() not in ["good", "bad"]:
        return JsonResponse({"error": "feedback must be GOOD or BAD"}, status=400)

    if not duo_match_id:
        return JsonResponse({"error": "duo_match_id is required"}, status=400)

    if not feedback:
        return JsonResponse({"error": "feedback is required"}, status=400)

    if DuoMatchFeedback.objects.filter(duo_match_id=duo_match_id, user=me).exists():
        duo_match_feedback = DuoMatchFeedback.objects.get(
            duo_match_id=duo_match_id, user=me
        )
        duo_match_feedback.rating = feedback.lower()
        duo_match_feedback.save()
    else:
        DuoMatchFeedback.objects.create(
            duo_match=DuoMatch.objects.get(id=duo_match_id),
            user=me,
            rating=feedback.lower(),
        )

    return JsonResponse({"message": "피드백을 제출했습니다."})


@login_required
def duo_match_report(request: WSGIRequest):
    me = request.user
    duo_match_id = request.GET.get("duo_match_id")

    if not duo_match_id:
        return redirect(request.META.get("HTTP_REFERER", "recommend:history"))

    duo_match = DuoMatch.objects.get(id=duo_match_id)

    if DuoMatchReport.objects.filter(duo_match=duo_match, user=me).exists():
        return redirect(request.META.get("HTTP_REFERER", "recommend:history"))

    if duo_match.user1 != me:
        return redirect(request.META.get("HTTP_REFERER", "recommend:history"))

    return render(
        request, "recommend/duo_match_report.html", {"duo_match_id": duo_match_id}
    )


@login_required
@api_view(["POST"])
def duo_match_report_submit(request: WSGIRequest):
    me = request.user

    duo_match_id = request.data["duo_match_id"]
    reason = request.data["reason"]

    if not duo_match_id:
        return JsonResponse({"error": "duo_match_id is required"}, status=400)

    duo_match = DuoMatch.objects.get(id=duo_match_id)

    if duo_match.user1 != me:
        return JsonResponse(
            {"error": "You are not allowed to report this duo match"}, status=400
        )

    if not reason:
        return JsonResponse({"error": "report is required"}, status=400)

    DuoMatchReport.objects.create(
        duo_match=DuoMatch.objects.get(id=duo_match_id),
        user=me,
        reason=reason,
    )

    return JsonResponse({"message": "신고가 접수되었습니다."})
