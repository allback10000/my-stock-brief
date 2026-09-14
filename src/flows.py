"""외국인·기관 수급.

pykrx가 가져오는 KRX 확정치라 국내 종목만 되고, 장 마감 후에 반영된다.
장중 실시간 추정 수급이 필요하면 한국투자증권 KIS Open API를 붙여야 한다.
"""
import datetime as dt
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")


def _pick(row, *names):
    for n in names:
        if n in row.index:
            return float(row[n])
    return 0.0


def kr_flows(code, days=5):
    try:
        from pykrx import stock

        today = dt.datetime.now(KST).date()
        df = stock.get_market_trading_value_by_date(
            (today - dt.timedelta(days=days + 10)).strftime("%Y%m%d"),
            today.strftime("%Y%m%d"),
            code,
        )
        if df is None or df.empty:
            return None

        rows = df.tail(days)
        last = df.iloc[-1]
        foreign = [_pick(r, "외국인합계", "외국인") for _, r in rows.iterrows()]
        inst = [_pick(r, "기관합계", "기관") for _, r in rows.iterrows()]

        def streak(series):
            """같은 방향으로 연속 며칠인지."""
            if not series:
                return 0
            sign = 1 if series[-1] > 0 else -1
            n = 0
            for v in reversed(series):
                if (v > 0) == (sign > 0) and v != 0:
                    n += 1
                else:
                    break
            return n * sign

        return {
            "date": str(df.index[-1].date()),
            "foreign": _pick(last, "외국인합계", "외국인"),
            "institution": _pick(last, "기관합계", "기관"),
            "retail": _pick(last, "개인"),
            "foreign_5d": sum(foreign),
            "institution_5d": sum(inst),
            "foreign_streak": streak(foreign),
            "institution_streak": streak(inst),
        }
    except Exception:  # noqa: BLE001
        return None


def fetch(quote):
    if quote.get("market") != "KR":
        return None
    return kr_flows(quote["code"])
