"""시세와 일봉 히스토리. 국내는 네이버+pykrx, 미국은 yfinance."""
import datetime as dt
from zoneinfo import ZoneInfo

import requests

KST = ZoneInfo("Asia/Seoul")
NY = ZoneInfo("America/New_York")
NAVER_POLL = "https://polling.finance.naver.com/api/realtime/domestic/stock/{code}"
UA = {"User-Agent": "Mozilla/5.0", "Referer": "https://m.stock.naver.com/"}


def _num(v):
    if v in (None, ""):
        return None
    try:
        return float(str(v).replace(",", "").replace("%", "").replace("+", ""))
    except ValueError:
        return None


def kr_name(code):
    try:
        from pykrx import stock

        return stock.get_market_ticker_name(code) or code
    except Exception:  # noqa: BLE001
        return code


def session_progress(market, now=None):
    """장중 경과 비율. 거래량을 하루치로 환산할 때 쓴다."""
    now = now or dt.datetime.now(KST)
    if market == "KR":
        t = now.astimezone(KST)
        start = t.replace(hour=9, minute=0, second=0, microsecond=0)
        end = t.replace(hour=15, minute=30, second=0, microsecond=0)
    else:
        t = now.astimezone(NY)
        start = t.replace(hour=9, minute=30, second=0, microsecond=0)
        end = t.replace(hour=16, minute=0, second=0, microsecond=0)

    if t <= start:
        return 0.0
    if t >= end:
        return 1.0
    return (t - start).total_seconds() / (end - start).total_seconds()


def _kr_history(code, days=90):
    from pykrx import stock

    today = dt.datetime.now(KST).date()
    df = stock.get_market_ohlcv(
        (today - dt.timedelta(days=days * 2)).strftime("%Y%m%d"),
        today.strftime("%Y%m%d"),
        code,
    )
    if df is None or df.empty:
        return []
    return [
        {
            "date": str(i.date()),
            "open": float(r["시가"]),
            "high": float(r["고가"]),
            "low": float(r["저가"]),
            "close": float(r["종가"]),
            "volume": float(r["거래량"]),
        }
        for i, r in df.tail(days).iterrows()
    ]


def _us_history(symbol, days=90):
    import yfinance as yf

    df = yf.Ticker(symbol).history(period="6mo", auto_adjust=False)
    if df is None or df.empty:
        return []
    return [
        {
            "date": str(i.date()),
            "open": float(r["Open"]),
            "high": float(r["High"]),
            "low": float(r["Low"]),
            "close": float(r["Close"]),
            "volume": float(r["Volume"]),
        }
        for i, r in df.tail(days).iterrows()
    ]


def _kr_quote(code, name):
    out = {"code": code, "market": "KR", "name": name, "currency": "원"}
    r = requests.get(NAVER_POLL.format(code=code), headers=UA, timeout=10)
    d = r.json()["datas"][0]
    price = _num(d.get("nv"))
    prev = _num(d.get("sv"))
    change = _num(d.get("cv")) or 0.0
    pct = _num(d.get("cr")) or 0.0
    if d.get("rf") in ("4", "5"):
        change, pct = -abs(change), -abs(pct)
    out.update(
        name=d.get("nm") or name,
        price=price,
        prev_close=prev,
        change=change,
        change_pct=pct,
        volume=_num(d.get("aq")),
    )
    return out


def _us_quote(symbol, name):
    import yfinance as yf

    out = {"code": symbol, "market": "US", "name": name, "currency": "$"}
    fi = yf.Ticker(symbol).fast_info
    price = fi.get("lastPrice") or fi.get("last_price")
    prev = fi.get("previousClose") or fi.get("previous_close")
    out.update(
        price=price,
        prev_close=prev,
        volume=fi.get("lastVolume") or fi.get("last_volume"),
    )
    if price and prev:
        out["change"] = price - prev
        out["change_pct"] = (price - prev) / prev * 100
    return out


def fetch(stock_cfg, with_history=True):
    code, market, name = stock_cfg["code"], stock_cfg["market"], stock_cfg.get("name")
    try:
        q = _kr_quote(code, name) if market == "KR" else _us_quote(code, name)
    except Exception as e:  # noqa: BLE001
        return {"code": code, "market": market, "name": name or code,
                "error": f"{type(e).__name__}: {e}"}

    q["avg_price"] = stock_cfg.get("avg_price")
    if with_history:
        try:
            q["history"] = _kr_history(code) if market == "KR" else _us_history(code)
        except Exception:  # noqa: BLE001
            q["history"] = []
    else:
        q["history"] = []

    hist = q.get("history") or []
    past = [h["volume"] for h in hist[-6:-1] if h["volume"]]
    if past and q.get("volume"):
        avg5 = sum(past) / len(past)
        progress = max(session_progress(market), 0.05)
        q["avg_volume_5d"] = avg5
        q["volume_ratio"] = q["volume"] / avg5
        q["volume_ratio_projected"] = (q["volume"] / progress) / avg5
    return q


def fetch_all(stocks, with_history=True):
    return [fetch(s, with_history) for s in stocks]
