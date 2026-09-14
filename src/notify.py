"""카톡 발송. out/message.json이 있을 때만 보낸다."""
import json
import os
import pathlib

from . import kakao

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAYLOAD = ROOT / "out" / "message.json"


def page_url():
    explicit = os.environ.get("PAGES_URL")
    if explicit:
        return explicit.rstrip("/") + "/"
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not repo:
        return None
    owner, name = repo.split("/")
    return f"https://{owner}.github.io/{name}/"


def main():
    if not PAYLOAD.exists():
        print("[info] 보낼 메시지가 없습니다.")
        return

    payload = json.loads(PAYLOAD.read_text(encoding="utf-8"))
    access, new_refresh = kakao.refresh_access_token(
        os.environ["KAKAO_REST_API_KEY"],
        os.environ["KAKAO_REFRESH_TOKEN"],
        os.environ.get("KAKAO_CLIENT_SECRET"),
    )
    kakao.rotate_if_needed(new_refresh)
    kakao.send_text(access, payload["text"], page_url() if payload.get("link") else None)
    print("[info] 발송 완료")


if __name__ == "__main__":
    main()
