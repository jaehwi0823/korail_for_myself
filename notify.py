"""KakaoTalk "send to me" notification.

Sends a text message to the authenticated Kakao user via the
talk/memo/default/send API. Kakao access tokens are short-lived, so each
send() refreshes one using the long-lived refresh token kept in .env.

Required .env keys:
    KAKAO_REST_API_KEY   - app REST API key (used as OAuth client_id)
    KAKAO_CLIENT_SECRET  - app client secret
    KAKAO_REFRESH_TOKEN  - long-lived refresh token (talk_message scope)
"""
import json
import os

import requests
from dotenv import load_dotenv, set_key

load_dotenv()

_ENV_PATH = ".env"
_TOKEN_URL = "https://kauth.kakao.com/oauth/token"
_SEND_URL = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
_LINK_URL = "https://www.letskorail.com"
_TIMEOUT = 10
_TEXT_LIMIT = 200  # Kakao text-template "text" field hard limit

REQUIRED_ENV = ("KAKAO_REST_API_KEY", "KAKAO_CLIENT_SECRET", "KAKAO_REFRESH_TOKEN")


def _refresh_access_token():
    """Exchange the refresh token for a fresh access token.

    Kakao returns a rotated refresh_token only when the current one nears
    expiry; when that happens, persist the new value back to .env.
    """
    resp = requests.post(
        _TOKEN_URL,
        data={
            "grant_type": "refresh_token",
            "client_id": os.environ["KAKAO_REST_API_KEY"],
            "client_secret": os.environ["KAKAO_CLIENT_SECRET"],
            "refresh_token": os.environ["KAKAO_REFRESH_TOKEN"],
        },
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    payload = resp.json()

    new_refresh = payload.get("refresh_token")
    if new_refresh and new_refresh != os.environ["KAKAO_REFRESH_TOKEN"]:
        set_key(_ENV_PATH, "KAKAO_REFRESH_TOKEN", new_refresh)
        os.environ["KAKAO_REFRESH_TOKEN"] = new_refresh

    return payload["access_token"]


def _send_to_me(access_token, text):
    """POST a text template to the send-to-me endpoint."""
    template = {
        "object_type": "text",
        "text": text,
        "link": {"web_url": _LINK_URL, "mobile_web_url": _LINK_URL},
    }
    resp = requests.post(
        _SEND_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        data={"template_object": json.dumps(template, ensure_ascii=False)},
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()


def send(text):
    """Send a KakaoTalk message to self. Returns True on success.

    Never raises: a notification failure must not affect the caller.
    """
    try:
        token = _refresh_access_token()
        _send_to_me(token, text[:_TEXT_LIMIT])
        return True
    except Exception as e:
        print(f"[warn] 카카오톡 알림 전송 실패: {e}")
        return False
