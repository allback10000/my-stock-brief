"""최초 1회만 로컬에서 실행. 리프레시 토큰을 발급받는다.

사전 준비 (Kakao Developers):
  1. 애플리케이션 생성 → REST API 키 확인
  2. 카카오 로그인 활성화 ON
  3. Redirect URI에 http://localhost:8765/callback 등록
  4. 동의항목 → 접근권한 → '카카오톡 메시지 전송(talk_message)' 이용 중 동의로 설정
  5. 앱 → 제품 링크 관리 → 웹 도메인에 GitHub Pages 주소 등록
     (등록하지 않으면 메시지의 링크 버튼이 동작하지 않는다)

실행:
  python scripts/auth.py --key <REST_API_KEY>
"""
import argparse
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer

import requests

REDIRECT = "http://localhost:8765/callback"
code_holder = {}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        code_holder["code"] = q.get("code", [None])[0]
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write("<h1>인증 완료. 터미널로 돌아가세요.</h1>".encode())

    def log_message(self, *a):
        pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--key", required=True, help="REST API 키")
    ap.add_argument("--client-secret", default=None)
    args = ap.parse_args()

    url = (
        "https://kauth.kakao.com/oauth/authorize?"
        + urllib.parse.urlencode({
            "client_id": args.key,
            "redirect_uri": REDIRECT,
            "response_type": "code",
            "scope": "talk_message",
        })
    )
    print("브라우저에서 로그인하세요:\n" + url)
    webbrowser.open(url)

    server = HTTPServer(("localhost", 8765), Handler)
    server.handle_request()

    code = code_holder.get("code")
    if not code:
        raise SystemExit("인가 코드를 받지 못했습니다. Redirect URI 등록을 확인하세요.")

    data = {
        "grant_type": "authorization_code",
        "client_id": args.key,
        "redirect_uri": REDIRECT,
        "code": code,
    }
    if args.client_secret:
        data["client_secret"] = args.client_secret

    body = requests.post("https://kauth.kakao.com/oauth/token", data=data, timeout=15).json()
    if "refresh_token" not in body:
        raise SystemExit(f"토큰 발급 실패: {body}")

    print("\n다음 값을 GitHub Secrets에 등록하세요.\n")
    print(f"KAKAO_REST_API_KEY   = {args.key}")
    print(f"KAKAO_REFRESH_TOKEN  = {body['refresh_token']}")
    print(f"\n(리프레시 토큰 유효기간: {body.get('refresh_token_expires_in', 0) // 86400}일)")


if __name__ == "__main__":
    main()
