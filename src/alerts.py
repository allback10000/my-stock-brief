"""조건 알림 판정과 중복 방지.

15분마다 돌기 때문에 같은 조건으로 하루 종일 카톡이 오면 안 된다.
state/alerts.json에 '오늘 이미 보낸 알림'을 기록해두고 건너뛴다.
급등락은 5%, 10%, 15% 구간이 바뀔 때마다 한 번씩 다시 알린다.
"""
import datetime as dt
import json
import pathlib
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")
STATE = pathlib.Path(__file__).resolve().parent.parent / "state" / "alerts.json"


def load_state():
    today = dt.datetime.now(KST).strftime("%Y-%m-%d")
    try:
        s = json.loads(STATE.read_text(encoding="utf-8"))
        if s.get("date") == today:
            return s
    except Exception:  # noqa: BLE001
        pass
    return {"date": today, "fired": []}


def save_state(state):
    STATE.parent.mkdir(exist_ok=True)
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")


def _won(v):
    sign = "+" if v > 0 else "−"
    a = abs(v)
    if a >= 1e8:
        return f"{sign}{a / 1e8:,.0f}억"
    return f"{sign}{a / 1e4:,.0f}만"


def _price(q):
    if q["market"] == "KR":
        return f"{q['price']:,.0f}원"
    return f"${q['price']:,.2f}"


def evaluate(quote, flow, level, thresholds):
    """이 종목에서 지금 울려야 할 알림 목록."""
    hits = []
    code = quote["code"]
    name = quote["name"]

    pct = quote.get("change_pct")
    t_pct = thresholds.get("change_pct", 5.0)
    if pct is not None and abs(pct) >= t_pct:
        bucket = int(abs(pct) // t_pct) * t_pct
        arrow = "🔺" if pct > 0 else "🔻"
        hits.append({
            "key": f"{code}:surge:{'up' if pct > 0 else 'down'}:{bucket:.0f}",
            "kind": "surge",
            "text": f"{arrow} {name} {pct:+.2f}% ({_price(quote)})",
        })

    ratio = quote.get("volume_ratio_projected")
    t_vol = thresholds.get("volume_ratio", 2.0)
    if ratio and ratio >= t_vol:
        bucket = int(ratio)
        hits.append({
            "key": f"{code}:volume:{bucket}",
            "kind": "volume",
            "text": f"📊 {name} 거래량 5일 평균의 {ratio:.1f}배 ({pct:+.2f}%)",
        })

    if flow:
        t_flow = thresholds.get("flow_krw", 5_000_000_000)
        for who, field, streak_field in (
            ("외국인", "foreign", "foreign_streak"),
            ("기관", "institution", "institution_streak"),
        ):
            v = flow.get(field) or 0
            if abs(v) >= t_flow:
                verb = "순매수" if v > 0 else "순매도"
                streak = flow.get(streak_field, 0)
                tail = f", {abs(streak)}일 연속" if abs(streak) >= 2 else ""
                hits.append({
                    "key": f"{code}:flow:{field}:{flow['date']}",
                    "kind": "flow",
                    "text": f"💰 {name} {who} {verb} {_won(v)}원{tail}",
                })

    if level and quote.get("price"):
        p = quote["price"]
        if p <= level["stop_loss"]:
            hits.append({
                "key": f"{code}:stop",
                "kind": "stop",
                "text": f"⚠️ {name} 손절선 도달 ({_price(quote)}, 설정 {level['stop_loss_pct']}%)",
            })
        elif p >= level["take_profit"]:
            hits.append({
                "key": f"{code}:target",
                "kind": "target",
                "text": f"🎯 {name} 목표가 도달 ({_price(quote)}, 설정 +{level['take_profit_pct']}%)",
            })

    return hits


def filter_new(hits, state):
    fired = set(state["fired"])
    fresh = [h for h in hits if h["key"] not in fired]
    state["fired"].extend(h["key"] for h in fresh)
    return fresh
