import json
import os
from enum import Enum

import boto3
from dotenv import load_dotenv


class Env(str, Enum):
    Dev = "development"
    Prod = "production"
    Local = "local"


# .env 파일에서 환경 변수 로드
load_dotenv()

_env = Env(os.getenv("ENVIRONMENT", Env.Local))


def _get_config(secret_arn: str, key=None):
    client = boto3.client(
        service_name="secretsmanager",
        region_name="ap-northeast-2",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    )
    get_secret_value_response = client.get_secret_value(SecretId=secret_arn)
    secret = get_secret_value_response["SecretString"]
    if key:
        return json.loads(secret)[key]
    return secret


def _get_allowed_hosts():
    if _env == Env.Prod:
        return [
            "dev.duofinder.kr",
            "duofinder.kr",
        ]
    else:
        return [
            "local.duofinder.kr",
            "localhost",
            "127.0.0.1",
        ]


class Database:
    def __init__(self, env: Env):
        if env == Env.Local:
            self.name = os.getenv("DATABASE_NAME", "duofinder")
            self.user = os.getenv("DATABASE_USER", "duofinder")
            self.password = os.getenv("DATABASE_PASSWORD", "duofinder")
            self.host = os.getenv("DATABASE_HOST", "duofinder-postgres")
            self.port = os.getenv("DATABASE_PORT", "5432")
        else:
            _secret_arn = os.getenv("DATABASE_SECRET_ARN")

            self.name = _get_config(_secret_arn, "dbname")
            self.user = _get_config(_secret_arn, "username")
            self.password = _get_config(_secret_arn, "password")
            self.host = _get_config(_secret_arn, "host")
            self.port = _get_config(_secret_arn, "port")

    def to_dict(self):
        return {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": self.name,
            "USER": self.user,
            "PASSWORD": self.password,
            "HOST": self.host,
            "PORT": self.port,
        }


class Riot:
    def __init__(self, env: Env):
        if env == Env.Local:
            self.api_key = os.getenv("RIOT_API_KEY")
            self.rso_client_id = os.getenv("RIOT_RSO_CLIENT_ID")
            self.rso_client_secret = os.getenv("RIOT_RSO_CLIENT_SECRET")
        else:
            _secret_arn = os.getenv("RIOT_SECRET_ARN")

            self.api_key = _get_config(_secret_arn, "RIOT_API_KEY")
            self.rso_client_id = _get_config(_secret_arn, "RIOT_RSO_CLIENT_ID")
            self.rso_client_secret = _get_config(_secret_arn, "RIOT_RSO_CLIENT_SECRET")


class Discord:
    def __init__(self, env: Env):
        if env == Env.Local:
            self.client_id = os.getenv("DISCORD_CLIENT_ID")
            self.client_secret = os.getenv("DISCORD_CLIENT_SECRET")
        else:
            _secret_arn = os.getenv("DISCORD_SECRET_ARN")

            self.client_id = _get_config(_secret_arn, "DISCORD_CLIENT_ID")
            self.client_secret = _get_config(_secret_arn, "DISCORD_CLIENT_SECRET")


class SecretKey:
    def __init__(self, env: Env):
        if env == Env.Local:
            self.secret_key = os.getenv(
                "WEB_SECRET_KEY",
                "secret",
            )
        else:
            _secret_arn = os.getenv("SECRET_KEY_SECRET_ARN")

            self.secret_key = _get_config(_secret_arn, "WEB_SECRET_KEY")


class S3:
    def __init__(self, env: Env):
        self.bucket_name = os.getenv("S3_BUCKET_NAME")
        self.s3_domain = os.getenv("S3_DOMAIN")
        self.s3_object_parameters = {
            "CacheControl": "max-age=86400",  # 1 day
        }
        

class Sentry:
    def __init__(self, env: Env):
        if env == Env.Local:
            self.dsn = os.getenv("SENTRY_DSN")
        else:
            _secret_arn = os.getenv("SENTRY_SECRET_ARN")

            self.dsn = _get_config(_secret_arn, "SENTRY_DSN")


class Config:
    def __init__(self):
        self.Env = _env
        self.db = Database(_env)
        self.riot = Riot(_env)
        self.discord = Discord(_env)
        self.s3 = S3(_env)
        self.sentry = Sentry(_env)

        self.Debug = True if _env == Env.Local else False
        self.secret_key = SecretKey(_env).secret_key

        self.allowed_hosts = _get_allowed_hosts()


config = Config()


def get_config():
    return config
