"""종목 관련 뉴스 헤드라인."""
import html
import os
import re

import requests

NAVER_NEWS = "https://openapi.naver.com/v1/search/news.json"


def _strip(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s or "")).strip()


def kr_news(name, limit=4):
    cid = os.environ.get("NAVER_CLIENT_ID")
    secret = os.environ.get("NAVER_CLIENT_SECRET")
    if not (cid and secret):
        return []
    try:
        r = requests.get(
            NAVER_NEWS,
            headers={"X-Naver-Client-Id": cid, "X-Naver-Client-Secret": secret},
            params={"query": name, "display": limit, "sort": "date"},
            timeout=10,
        )
        return [
            {"title": _strip(i["title"]), "url": i.get("originallink") or i["link"],
             "date": i.get("pubDate", "")}
            for i in r.json().get("items", [])
        ]
    except Exception:  # noqa: BLE001
        return []


def us_news(symbol, limit=4):
    try:
        import yfinance as yf

        items = yf.Ticker(symbol).news or []
        out = []
        for i in items[:limit]:
            c = i.get("content", i)
            title = c.get("title")
            url = (c.get("canonicalUrl") or {}).get("url") or i.get("link", "")
            if title:
                out.append({"title": title, "url": url, "date": c.get("pubDate", "")})
        return out
    except Exception:  # noqa: BLE001
        return []


def fetch(quote, limit=4):
    if quote["market"] == "KR":
        return kr_news(quote["name"], limit)
    return us_news(quote["code"], limit)
