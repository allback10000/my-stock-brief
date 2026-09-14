"""watchlist.json 읽기·쓰기와 종목 추가/삭제."""
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
PATH = ROOT / "watchlist.json"

KR_CODE = re.compile(r"^\d{6}$")
US_CODE = re.compile(r"^[A-Z][A-Z.\-]{0,9}$")


def load():
    data = json.loads(PATH.read_text(encoding="utf-8"))
    data.setdefault("defaults", {"stop_loss_pct": -7, "take_profit_pct": 15})
    data.setdefault("alerts", {})
    data.setdefault("stocks", [])
    return data


def save(data):
    PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def guess_market(code):
    if KR_CODE.match(code):
        return "KR"
    if US_CODE.match(code.upper()):
        return "US"
    raise ValueError(f"종목코드 형식을 알 수 없습니다: {code}")


def normalize(code, market=None):
    market = (market or guess_market(code)).upper()
    return (code if market == "KR" else code.upper()), market


def rules_for(stock, defaults):
    """종목별 손절·익절 규칙. 개별 설정이 없으면 기본값을 쓴다."""
    return {
        "stop_loss_pct": stock.get("stop_loss_pct", defaults.get("stop_loss_pct", -7)),
        "take_profit_pct": stock.get(
            "take_profit_pct", defaults.get("take_profit_pct", 15)
        ),
    }


def add(code, market=None, name=None, avg_price=None,
        stop_loss_pct=None, take_profit_pct=None):
    data = load()
    code, market = normalize(code, market)

    for s in data["stocks"]:
        if s["code"] == code and s["market"] == market:
            if name:
                s["name"] = name
            if avg_price is not None:
                s["avg_price"] = avg_price
            if stop_loss_pct is not None:
                s["stop_loss_pct"] = stop_loss_pct
            if take_profit_pct is not None:
                s["take_profit_pct"] = take_profit_pct
            save(data)
            return f"{code} 정보를 수정했습니다."

    entry = {"code": code, "market": market, "name": name or code, "avg_price": avg_price}
    if stop_loss_pct is not None:
        entry["stop_loss_pct"] = stop_loss_pct
    if take_profit_pct is not None:
        entry["take_profit_pct"] = take_profit_pct

    data["stocks"].append(entry)
    save(data)
    return f"{entry['name']}({code}) 추가했습니다. 현재 {len(data['stocks'])}종목."


def remove(code, market=None):
    data = load()
    code, market = normalize(code, market)
    before = len(data["stocks"])
    data["stocks"] = [
        s for s in data["stocks"] if not (s["code"] == code and s["market"] == market)
    ]
    if len(data["stocks"]) == before:
        return f"{code}는 목록에 없습니다."
    save(data)
    return f"{code} 삭제했습니다. 남은 {len(data['stocks'])}종목."


def listing():
    data = load()
    if not data["stocks"]:
        return "등록된 종목이 없습니다."
    lines = []
    for s in data["stocks"]:
        r = rules_for(s, data["defaults"])
        avg = ""
        if s.get("avg_price"):
            p = s["avg_price"]
            avg = f", 평단 {p:,.0f}" if float(p).is_integer() else f", 평단 {p:,.2f}"
        lines.append(
            f"[{s['market']}] {s['name']} ({s['code']})"
            f"{avg}, 손절 {r['stop_loss_pct']}% / 익절 +{r['take_profit_pct']}%"
        )
    return "\n".join(lines)
