"""카카오 '나에게 보내기' + 리프레시 토큰 자동 로테이션."""
import base64
import json
import os

import requests

KAUTH = "https://kauth.kakao.com/oauth/token"
MEMO = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
GITHUB = "https://api.github.com"


def refresh_access_token(rest_api_key, refresh_token, client_secret=None):
    """액세스 토큰(6시간짜리)을 새로 받는다.

    리프레시 토큰의 남은 기간이 1개월 미만이면 응답에 새 refresh_token이
    함께 온다. 그 경우 반드시 저장해야 두 달 뒤에 죽지 않는다.
    """
    data = {
        "grant_type": "refresh_token",
        "client_id": rest_api_key,
        "refresh_token": refresh_token,
    }
    if client_secret:
        data["client_secret"] = client_secret

    r = requests.post(KAUTH, data=data, timeout=15)
    if r.status_code != 200:
        raise RuntimeError(f"토큰 갱신 실패 {r.status_code}: {r.text}")

    body = r.json()
    return body["access_token"], body.get("refresh_token")


def send_text(access_token, text, link_url=None, button_title="전체 브리핑 보기"):
    """나와의 채팅방으로 텍스트 메시지 발송. text는 200자까지만 표시된다."""
    template = {
        "object_type": "text",
        "text": text[:200],
        "link": {"web_url": link_url, "mobile_web_url": link_url} if link_url else {},
    }
    if link_url:
        template["button_title"] = button_title

    r = requests.post(
        MEMO,
        headers={"Authorization": f"Bearer {access_token}"},
        data={"template_object": json.dumps(template, ensure_ascii=False)},
        timeout=15,
    )
    if r.status_code != 200:
        raise RuntimeError(f"메시지 발송 실패 {r.status_code}: {r.text}")
    return r.json()


def update_repo_secret(repo, name, value, pat):
    """새 리프레시 토큰을 GitHub Secret에 덮어쓴다.

    GitHub Actions는 실행 간 상태가 남지 않으므로, 토큰이 갱신될 때마다
    Secret 자체를 갱신해야 한다. 기본 GITHUB_TOKEN은 Secret 쓰기 권한이
    없으므로 별도 PAT(Secrets: read and write)이 필요하다.
    """
    from nacl import encoding, public

    headers = {
        "Authorization": f"Bearer {pat}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    key = requests.get(
        f"{GITHUB}/repos/{repo}/actions/secrets/public-key", headers=headers, timeout=15
    ).json()

    sealed = public.SealedBox(
        public.PublicKey(key["key"].encode(), encoding.Base64Encoder)
    ).encrypt(value.encode())

    r = requests.put(
        f"{GITHUB}/repos/{repo}/actions/secrets/{name}",
        headers=headers,
        json={
            "encrypted_value": base64.b64encode(sealed).decode(),
            "key_id": key["key_id"],
        },
        timeout=15,
    )
    if r.status_code not in (201, 204):
        raise RuntimeError(f"Secret 갱신 실패 {r.status_code}: {r.text}")


def rotate_if_needed(new_refresh_token):
    """리프레시 토큰이 새로 발급됐을 때만 Secret을 갱신한다."""
    if not new_refresh_token:
        return False
    repo = os.environ.get("GITHUB_REPOSITORY")
    pat = os.environ.get("GH_PAT")
    if not (repo and pat):
        print("[warn] 새 리프레시 토큰이 발급됐지만 GH_PAT이 없어 저장하지 못했습니다.")
        print("[warn] 이대로 두면 최대 2개월 뒤 알림이 멈춥니다.")
        return False
    update_repo_secret(repo, "KAKAO_REFRESH_TOKEN", new_refresh_token, pat)
    print("[info] 리프레시 토큰을 새로 저장했습니다.")
    return True
