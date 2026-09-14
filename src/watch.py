"""조건 알림 감시. 장중 15분마다 돈다.

등락률 ±5%, 거래량 급증, 외국인·기관 수급, 손절선·목표가 도달을 본다.
같은 조건으로 하루 종일 알림이 오지 않도록 state/alerts.json에 기록한다.
"""
import datetime as dt
import json
import pathlib
from zoneinfo import ZoneInfo

from . import alerts, config, flows, levels, quotes, render

KST = ZoneInfo("Asia/Seoul")
ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "out"


def session_open(now=None):
    """국내장 또는 미국 정규장이 열려 있는 시장 목록."""
    now = now or dt.datetime.now(KST)
    if now.weekday() >= 5:
        return []

    open_markets = []
    minutes = now.hour * 60 + now.minute
    if 9 * 60 <= minutes <= 15 * 60 + 30:
        open_markets.append("KR")

    ny = now.astimezone(ZoneInfo("America/New_York"))
    if ny.weekday() < 5 and (9 * 60 + 30) <= (ny.hour * 60 + ny.minute) <= 16 * 60:
        open_markets.append("US")
    return open_markets


def main():
    now = dt.datetime.now(KST)
    live = session_open(now)
    cfg = config.load()
    thresholds = cfg.get("alerts", {})

    # 수급은 장 마감 후 확정치라, 국내장이 닫힌 뒤에도 한 번은 본다.
    after_kr_close = now.weekday() < 5 and 15 * 60 + 40 <= now.hour * 60 + now.minute <= 20 * 60

    targets = [s for s in cfg["stocks"] if s["market"] in live]
    if after_kr_close:
        targets += [
            s for s in cfg["stocks"]
            if s["market"] == "KR" and s not in targets
        ]

    if not targets:
        print(f"[info] 감시 대상 없음 (열린 장: {live or '없음'})")
        return

    state = alerts.load_state()
    hits = []

    for s in targets:
        q = quotes.fetch(s)
        if q.get("error"):
            continue
        flow = flows.fetch(q) if (s["market"] == "KR" and after_kr_close) else None
        lv = levels.compute(q, config.rules_for(s, cfg["defaults"]))
        hits += alerts.evaluate(q, flow, lv, thresholds)

    fresh = alerts.filter_new(hits, state)
    alerts.save_state(state)

    if not fresh:
        print(f"[info] 조건 충족 없음 ({len(targets)}종목 확인)")
        return

    OUT.mkdir(exist_ok=True)
    (OUT / "message.json").write_text(
        json.dumps(
            {"text": render.alert_message(fresh), "link": True},
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    print(f"[info] 알림 {len(fresh)}건: " + " / ".join(h["kind"] for h in fresh))


if __name__ == "__main__":
    main()
