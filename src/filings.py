"""공시. 국내는 DART OpenAPI, 미국은 SEC EDGAR."""
import datetime as dt
import io
import os
import zipfile
import xml.etree.ElementTree as ET

import requests

DART_CORPCODE = "https://opendart.fss.or.kr/api/corpCode.xml"
DART_LIST = "https://opendart.fss.or.kr/api/list.json"
SEC_TICKERS = "https://www.sec.gov/files/company_tickers.json"
SEC_SUBMISSIONS = "https://data.sec.gov/submissions/CIK{cik}.json"
SEC_UA = {"User-Agent": os.environ.get("SEC_USER_AGENT", "stock-brief contact@example.com")}

_corp_cache = None


def _dart_corp_map(api_key):
    """종목코드 → DART 고유번호 매핑. 실행당 한 번만 받는다."""
    global _corp_cache
    if _corp_cache is not None:
        return _corp_cache
    r = requests.get(DART_CORPCODE, params={"crtfc_key": api_key}, timeout=60)
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        xml = z.read(z.namelist()[0])
    _corp_cache = {}
    for el in ET.fromstring(xml).iter("list"):
        stock = (el.findtext("stock_code") or "").strip()
        if stock:
            _corp_cache[stock] = el.findtext("corp_code").strip()
    return _corp_cache


def kr_filings(code, days=3, limit=5):
    api_key = os.environ.get("DART_API_KEY")
    if not api_key:
        return []
    try:
        corp = _dart_corp_map(api_key).get(code)
        if not corp:
            return []
        today = dt.date.today()
        r = requests.get(
            DART_LIST,
            params={
                "crtfc_key": api_key,
                "corp_code": corp,
                "bgn_de": (today - dt.timedelta(days=days)).strftime("%Y%m%d"),
                "end_de": today.strftime("%Y%m%d"),
                "page_count": limit,
            },
            timeout=15,
        )
        return [
            {
                "title": i["report_nm"],
                "date": i["rcept_dt"],
                "url": f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={i['rcept_no']}",
            }
            for i in r.json().get("list", [])[:limit]
        ]
    except Exception:  # noqa: BLE001
        return []


def us_filings(symbol, limit=4):
    try:
        table = requests.get(SEC_TICKERS, headers=SEC_UA, timeout=15).json()
        cik = next(
            (str(v["cik_str"]).zfill(10) for v in table.values()
             if v["ticker"].upper() == symbol.upper()),
            None,
        )
        if not cik:
            return []
        recent = requests.get(
            SEC_SUBMISSIONS.format(cik=cik), headers=SEC_UA, timeout=15
        ).json()["filings"]["recent"]
        out = []
        for form, date, acc, doc in zip(
            recent["form"], recent["filingDate"],
            recent["accessionNumber"], recent["primaryDocument"]
        ):
            acc_plain = acc.replace("-", "")
            out.append({
                "title": form,
                "date": date,
                "url": f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc_plain}/{doc}",
            })
            if len(out) >= limit:
                break
        return out
    except Exception:  # noqa: BLE001
        return []


def fetch(quote):
    if quote["market"] == "KR":
        return kr_filings(quote["code"])
    return us_filings(quote["code"])
