"""정기 브리핑 (07:30 / 16:00 / 21:00)."""
import argparse
import datetime as dt
import json
import os
import pathlib
from zoneinfo import ZoneInfo

from . import config, filings, flows, levels, macro, news, quotes, render, summarize

KST = ZoneInfo("Asia/Seoul")
ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
OUT = ROOT / "out"


def detect_slot():
    h = dt.datetime.utcnow().hour
    if h in (22, 23, 0):
        return "morning"
    if h in (6, 7, 8):
        return "close"
    return "evening"


def collect(cfg):
    items = []
    for s in cfg["stocks"]:
        q = quotes.fetch(s)
        item = {"quote": q, "news": [], "filings": [], "flows": None, "levels": None}
        if not q.get("error"):
            item["news"] = news.fetch(q)
            item["filings"] = filings.fetch(q)
            item["flows"] = flows.fetch(q)
            item["levels"] = levels.compute(q, config.rules_for(s, cfg["defaults"]))
        items.append(item)
    return items


def ai_payload(slot, items, macro_data):
    return {
        "slot": slot,
        "macro": macro_data,
        "stocks": [
            {
                "code": i["quote"]["code"],
                "name": i["quote"]["name"],
                "market": i["quote"]["market"],
                "price": i["quote"].get("price"),
                "change_pct": i["quote"].get("change_pct"),
                "volume_vs_5d_avg": i["quote"].get("volume_ratio_projected"),
                "levels": i["levels"],
                "flows": i["flows"],
                "filings": [f["title"] for f in i["filings"][:3]],
                "news": [n["title"] for n in i["news"][:4]],
            }
            for i in items
            if not i["quote"].get("error")
        ],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slot", choices=["morning", "close", "evening"])
    args = ap.parse_args()

    slot = args.slot or os.environ.get("SLOT") or detect_slot()
    cfg = config.load()
    if not cfg["stocks"]:
        print("[info] 등록된 종목이 없습니다.")
        return

    items = collect(cfg)
    macro_data = macro.snapshot()
    ai = summarize.build(slot, ai_payload(slot, items, macro_data))

    DOCS.mkdir(exist_ok=True)
    (DOCS / ".nojekyll").touch()
    page = render.render(slot, items, ai, macro_data)
    (DOCS / "index.html").write_text(page, encoding="utf-8")

    archive = DOCS / "archive"
    archive.mkdir(exist_ok=True)
    stamp = dt.datetime.now(KST).strftime("%Y-%m-%d-%H%M")
    (archive / f"{stamp}.html").write_text(page, encoding="utf-8")

    OUT.mkdir(exist_ok=True)
    (OUT / "message.json").write_text(
        json.dumps(
            {"text": render.brief_message(slot, items, ai), "link": True},
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    print(f"[info] {slot} 브리핑 완료 · {len(items)}종목")


if __name__ == "__main__":
    main()
