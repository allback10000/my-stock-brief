"""가격대 계산.

여기 있는 값은 전부 과거 데이터에서 나온 산술 결과다. 예측이 아니다.
'오늘 예상 변동폭'은 최근 변동성이 그대로 이어진다고 가정했을 때의
통계적 범위이지, 오늘 그 안에서 움직인다는 보장이 아니다.
손절가와 목표가는 watchlist.json에 적어둔 본인 규칙을 가격으로 환산한 것이다.
"""


def sma(closes, n):
    if len(closes) < n:
        return None
    return sum(closes[-n:]) / n


def atr(history, n=14):
    if len(history) < n + 1:
        return None
    trs = []
    for prev, cur in zip(history[-(n + 1):-1], history[-n:]):
        trs.append(max(
            cur["high"] - cur["low"],
            abs(cur["high"] - prev["close"]),
            abs(cur["low"] - prev["close"]),
        ))
    return sum(trs) / len(trs)


def pivots(bar):
    """전일 고가·저가·종가로 만드는 표준 피벗 포인트."""
    p = (bar["high"] + bar["low"] + bar["close"]) / 3
    return {
        "pivot": p,
        "r1": 2 * p - bar["low"],
        "s1": 2 * p - bar["high"],
        "r2": p + (bar["high"] - bar["low"]),
        "s2": p - (bar["high"] - bar["low"]),
    }


def compute(quote, rules):
    hist = quote.get("history") or []
    if len(hist) < 20:
        return None

    closes = [h["close"] for h in hist]
    base = quote.get("price") or closes[-1]
    prev = hist[-1]
    a = atr(hist)

    out = {
        "base_price": base,
        "atr": a,
        "expected_low": base - a if a else None,
        "expected_high": base + a if a else None,
        "atr_pct": (a / base * 100) if a and base else None,
        "ma20": sma(closes, 20),
        "ma60": sma(closes, 60),
        "high_20d": max(h["high"] for h in hist[-20:]),
        "low_20d": min(h["low"] for h in hist[-20:]),
        **pivots(prev),
    }

    # 손절·목표가는 평단가가 있으면 평단 기준, 없으면 현재가 기준.
    anchor = quote.get("avg_price") or base
    out["anchor"] = anchor
    out["anchor_is_avg"] = bool(quote.get("avg_price"))
    out["stop_loss"] = anchor * (1 + rules["stop_loss_pct"] / 100)
    out["take_profit"] = anchor * (1 + rules["take_profit_pct"] / 100)
    out["stop_loss_pct"] = rules["stop_loss_pct"]
    out["take_profit_pct"] = rules["take_profit_pct"]
    if base:
        out["to_stop_pct"] = (out["stop_loss"] - base) / base * 100
        out["to_target_pct"] = (out["take_profit"] - base) / base * 100
    return out
