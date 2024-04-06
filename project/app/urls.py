from django.urls import path, include
from allauth.socialaccount.providers.discord.urls import (
    urlpatterns as discord_urlpatterns,
)
from project import settings
from .views import (
    duo_match_feedback,
    duo_match_report,
    duo_match_report_submit,
    index,
    get_account_by_summoner_name,
    recommend_ai,
    recommend_result,
    riot_sign_on_callback,
    riot_txt,
    save_summoner,
    terms_of_service,
    privacy_policy,
    riot_sign_on,
    riot_account_refresh,
    riot_account_disconnect,
    inference,
    get_duo_match,
    get_duo_match_history,
    sign_out,
)

urlpatterns = [
    # static
    path("riot.txt", riot_txt),
    # legal
    path(
        "tos",
        terms_of_service,
        name="terms-of-service",
    ),
    path(
        "privacy",
        privacy_policy,
        name="privacy-policy",
    ),
    # views
    path(
        "",
        index,
        name="home",
    ),
    path(
        "summoner/",
        get_account_by_summoner_name,
        name="summoner",
    ),
    path(
        "recommend-ai/",
        recommend_ai,
        name="recommend-ai",
    ),
    path(
        "recommend-result/",
        recommend_result,
        name="recommend-result",
    ),
    path(
        "profile/summoner",
        save_summoner,
        name="save-summoner-info",
    ),
    path(
        "match/duo",
        get_duo_match,
        name="get-duo-match",
    ),
    path(
        "match/duo/history",
        get_duo_match_history,
        name="get-duo-match-history",
    ),
    path(
        "riot-sign-on",
        riot_sign_on,
        name="riot-sign-on",
    ),
    path(
        "riot-account-refresh",
        riot_account_refresh,
        name="riot-account-refresh",
    ),
    path(
        "riot-account-disconnect",
        riot_account_disconnect,
        name="riot-account-disconnect",
    ),
    path(
        "accounts/riot/callback",
        riot_sign_on_callback,
        name="riot-sign-on-callback",
    ),
    # api
    path(
        "recommend/inference",
        inference,
        name="inference",
    ),
    # allauth
    path(
        "accounts/",
        include(discord_urlpatterns),
    ),
    path(
        "sign-out",
        sign_out,
        name="sign-out",
    ),
    path(
        "duo-match-feedback",
        duo_match_feedback,
        name="duo-match-feedback",
    ),
    path(
        "duo-match-report",
        duo_match_report,
        name="duo-match-report",
    ),
    path(
        "duo-match-report-submit",
        duo_match_report_submit,
        name="duo-match-report-submit",
    ),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
