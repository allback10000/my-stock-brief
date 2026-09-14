"""브리핑 HTML. 세 단계 설명은 페이지 위 토글로 바꿔 본다."""
import datetime as dt
import html
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")
PRETENDARD = (
    "https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/"
    "variable/pretendardvariable-dynamic-subset.min.css"
)
SLOT_LABEL = {"morning": "개장 전", "close": "장 마감", "evening": "미국장 개장 전"}
LEVELS = [("middle", "쉽게"), ("high", "보통"), ("college", "자세히")]

CSS = """
:root{--paper:#f5f6f4;--ink:#16181c;--muted:#6b7078;--rule:#dfe1de;--up:#d0342c;--down:#1150c4}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--paper);color:var(--ink);
 font-family:'Pretendard Variable',Pretendard,-apple-system,system-ui,sans-serif;
 font-size:16px;line-height:1.7;font-feature-settings:'tnum' 1}
main{max-width:34rem;margin:0 auto;padding:2.25rem 1.25rem 5rem}
a{color:inherit}
a:focus-visible,button:focus-visible{outline:2px solid var(--ink);outline-offset:2px}
.up{color:var(--up)}.down{color:var(--down)}.flat{color:var(--muted)}

.masthead{color:var(--muted);font-size:.875rem;margin:0 0 1.25rem}
.masthead strong{color:var(--ink);font-weight:600}

.macro{font-size:.8125rem;color:var(--muted);margin:0 0 1.75rem;
 display:flex;flex-wrap:wrap;gap:.25rem 1rem;line-height:1.5}
.macro b{font-weight:500;color:var(--ink)}

.toggle{display:flex;gap:1.25rem;border-top:1px solid var(--rule);
 border-bottom:1px solid var(--rule);padding:.6rem 0;margin:0 0 2rem}
.toggle button{background:none;border:0;padding:0;cursor:pointer;font:inherit;
 font-size:.9375rem;color:var(--muted);border-bottom:2px solid transparent}
.toggle button[aria-pressed="true"]{color:var(--ink);font-weight:600;border-bottom-color:var(--ink)}

.lede{font-size:1.0625rem;margin:0 0 2.75rem}
[data-level=middle] .lv:not(.lv-middle),
[data-level=high] .lv:not(.lv-high),
[data-level=college] .lv:not(.lv-college){display:none}

.stock{border-top:1px solid var(--rule);padding-top:1.5rem;margin-bottom:3.25rem}
.stock h2{font-size:.9375rem;font-weight:600;margin:0;display:flex;
 justify-content:space-between;gap:1rem}
.stock h2 span{color:var(--muted);font-weight:400}
.readout{display:flex;align-items:baseline;gap:1rem;flex-wrap:wrap;margin:.5rem 0 1.25rem}
.delta{font-size:clamp(2.5rem,12vw,3.5rem);font-weight:650;letter-spacing:-.035em;line-height:1}
.price{font-size:1.0625rem;font-weight:500}
.price em{font-style:normal;color:var(--muted);font-weight:400}
.brief{margin:0 0 1.5rem}

.levels{display:grid;grid-template-columns:auto 1fr;gap:.15rem 1rem;
 font-size:.9375rem;margin:0 0 1.5rem}
.levels dt{color:var(--muted)}
.levels dd{margin:0;font-variant-numeric:tabular-nums}

.plan{border-left:2px solid var(--rule);padding-left:1rem;margin:0 0 1.5rem;font-size:.9375rem}
.plan p{margin:0 0 .6rem}
.plan p:last-child{margin:0}
.plan b{font-weight:600}
.flow{color:var(--muted);font-size:.9375rem;margin:0 0 1.25rem}

.links{margin:0;padding:0;list-style:none;font-size:.9375rem}
.links li{display:flex;gap:.75rem;padding:.3rem 0}
.links time{color:var(--muted);flex:0 0 auto}
.links a{text-decoration-color:var(--rule);text-underline-offset:3px}
.links a:hover{text-decoration-color:var(--ink)}

.colophon{border-top:1px solid var(--rule);padding-top:1.25rem;color:var(--muted);font-size:.8125rem}
.colophon p{margin:0 0 .6rem}
.err{color:var(--muted);font-size:.9375rem}
"""

JS = """
const main=document.querySelector('main');
document.querySelectorAll('.toggle button').forEach(b=>{
 b.addEventListener('click',()=>{
  main.dataset.level=b.dataset.lv;
  document.querySelectorAll('.toggle button').forEach(x=>
   x.setAttribute('aria-pressed', x===b));
 });
});
"""


def _e(s):
    return html.escape(str(s), quote=True)


def money(v, market, dp=None):
    if v is None:
        return "—"
    if market == "KR":
        return f"{v:,.0f}원"
    return f"${v:,.{dp if dp is not None else 2}f}"


def fmt_delta(pct):
    if pct is None:
        return "—"
    mark = "▲" if pct > 0 else ("▼" if pct < 0 else "―")
    return f"{mark}{abs(pct):.2f}%"


def dcls(pct):
    if pct is None or pct == 0:
        return "flat"
    return "up" if pct > 0 else "down"


def fmt_volume(v, market):
    if not v:
        return None
    if market == "KR":
        if v >= 1e8:
            return f"{v / 1e8:.2f}억주"
        if v >= 1e4:
            return f"{v / 1e4:.1f}만주"
    else:
        if v >= 1e6:
            return f"{v / 1e6:.1f}M"
    return f"{v:,.0f}"


def fmt_won(v):
    sign = "+" if v > 0 else "−"
    a = abs(v)
    return f"{sign}{a / 1e8:,.0f}억" if a >= 1e8 else f"{sign}{a / 1e4:,.0f}만"


def _tiers(obj, cls="brief"):
    """세 단계 텍스트를 한꺼번에 넣어두고 CSS로 하나만 보여준다."""
    if not obj:
        return ""
    return "".join(
        f'<p class="{cls} lv lv-{k}">{_e(obj.get(k, ""))}</p>'
        for k, _ in LEVELS
        if obj.get(k)
    )


def _levels_block(lv, market):
    if not lv:
        return ""
    rows = []

    def add(label, value):
        rows.append(f"<dt>{_e(label)}</dt><dd>{value}</dd>")

    if lv.get("expected_low"):
        add("오늘 변동 예상폭",
            f'{money(lv["expected_low"], market)} ~ {money(lv["expected_high"], market)}'
            f' <span class="flat">(±{lv["atr_pct"]:.1f}%)</span>')
    if lv.get("ma20"):
        add("20일 / 60일선",
            f'{money(lv["ma20"], market)} / {money(lv.get("ma60"), market)}')
    add("피벗 (지지·저항)",
        f'{money(lv["s1"], market)} · {money(lv["pivot"], market)} · {money(lv["r1"], market)}')
    add("20일 고가 / 저가",
        f'{money(lv["high_20d"], market)} / {money(lv["low_20d"], market)}')

    anchor = "평단가" if lv["anchor_is_avg"] else "현재가"
    add(f'손절선 ({lv["stop_loss_pct"]}%)',
        f'<span class="down">{money(lv["stop_loss"], market)}</span>'
        f' <span class="flat">{anchor} 기준, 여기서 {lv["to_stop_pct"]:+.1f}%</span>')
    add(f'목표가 (+{lv["take_profit_pct"]}%)',
        f'<span class="up">{money(lv["take_profit"], market)}</span>'
        f' <span class="flat">{anchor} 기준, 여기서 {lv["to_target_pct"]:+.1f}%</span>')

    return f'<dl class="levels">{"".join(rows)}</dl>'


def _plan_block(plan):
    if not plan:
        return ""
    parts = []
    for k, label in (("morning", "오전"), ("afternoon", "오후")):
        if plan.get(k):
            parts.append(f"<p><b>{label}</b> {_e(plan[k])}</p>")
    return f'<div class="plan">{"".join(parts)}</div>' if parts else ""


def _stock_block(item, ai_stock):
    q = item["quote"]
    market = q["market"]
    out = [f'<section class="stock"><h2>{_e(q["name"])}<span>{_e(q["code"])}</span></h2>']

    if q.get("error"):
        return "".join(out) + '<p class="err">시세를 불러오지 못했습니다.</p></section>'

    pct = q.get("change_pct")
    vol = fmt_volume(q.get("volume"), market)
    ratio = q.get("volume_ratio_projected")
    vol_txt = ""
    if vol:
        vol_txt = f" <em>거래량 {vol}"
        if ratio:
            vol_txt += f", 5일 평균 대비 {ratio:.1f}배"
        vol_txt += "</em>"

    out.append(
        f'<div class="readout"><div class="delta {dcls(pct)}">{fmt_delta(pct)}</div>'
        f'<div class="price">{money(q.get("price"), market)}{vol_txt}</div></div>'
    )

    ai_stock = ai_stock or {}
    out.append(_tiers(ai_stock.get("brief")))
    out.append(_levels_block(item.get("levels"), market))
    out.append(_plan_block(ai_stock.get("plan")))

    f = item.get("flows")
    if f:
        streak = ""
        if abs(f.get("foreign_streak", 0)) >= 2:
            streak = f', 외국인 {abs(f["foreign_streak"])}일 연속'
        out.append(
            f'<p class="flow">{_e(f["date"])} 순매수 · 외국인 {fmt_won(f["foreign"])}원, '
            f'기관 {fmt_won(f["institution"])}원{streak}</p>'
        )

    rows = [
        f'<li><time>공시</time><a href="{_e(d["url"])}">{_e(d["title"])}</a></li>'
        for d in item.get("filings", [])[:3]
    ] + [
        f'<li><time>뉴스</time><a href="{_e(n["url"])}">{_e(n["title"])}</a></li>'
        for n in item.get("news", [])[:4]
    ]
    if rows:
        out.append(f'<ul class="links">{"".join(rows)}</ul>')

    return "".join(out) + "</section>"


def _macro_block(macro):
    if not macro:
        return ""
    spans = [
        f'<span>{_e(m["name"])} <b class="{dcls(m["change_pct"])}">'
        f'{m["change_pct"]:+.2f}%</b></span>'
        for m in macro
    ]
    return f'<div class="macro">{"".join(spans)}</div>'


def render(slot, items, ai, macro=None, now=None):
    now = now or dt.datetime.now(KST)
    label = SLOT_LABEL.get(slot, slot)
    date_line = now.strftime("%-m월 %-d일")
    ai = ai or {}
    per = ai.get("stocks", {})

    toggle = "".join(
        f'<button data-lv="{k}" aria-pressed="{"true" if k == "high" else "false"}">{v}</button>'
        for k, v in LEVELS
    )
    blocks = "".join(_stock_block(i, per.get(i["quote"]["code"])) for i in items)

    return f"""<!doctype html>
<html lang="ko"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{_e(date_line)} {_e(label)} 브리핑</title>
<link rel="stylesheet" href="{PRETENDARD}">
<style>{CSS}</style>
</head><body>
<main data-level="high">
 <p class="masthead"><strong>{_e(date_line)} {_e(label)}</strong><br>{now:%H:%M} 기준 · {len(items)}종목</p>
 {_macro_block(macro)}
 <div class="toggle">{toggle}</div>
 {_tiers(ai.get("overall"), "lede")}
 {blocks}
 <div class="colophon">
  <p>변동 예상폭은 최근 14일 평균 변동성(ATR)을 오늘에 그대로 적용한 값입니다.
  예측이 아니라 "최근엔 하루에 이 정도씩 움직였다"는 기록입니다.</p>
  <p>손절선과 목표가는 watchlist.json에 적어두신 규칙을 가격으로 환산한 것입니다.
  숫자를 바꾸려면 그 파일을 고치면 됩니다.</p>
  <p>시세는 네이버 금융과 Yahoo Finance, 공시는 DART와 SEC, 수급은 KRX에서 옵니다.
  수급은 장 마감 후 확정치라 하루 늦습니다.</p>
 </div>
</main>
<script>{JS}</script>
</body></html>
"""


def brief_message(slot, items, ai, limit=200):
    """정기 브리핑 카톡 본문."""
    label = SLOT_LABEL.get(slot, slot)
    lines = [f"📊 {dt.datetime.now(KST):%m/%d} {label}"]
    for i in items:
        q = i["quote"]
        if q.get("error"):
            continue
        lines.append(
            f'{q["name"]} {money(q.get("price"), q["market"])} {fmt_delta(q.get("change_pct"))}'
        )
    text = "\n".join(lines)

    tail = ((ai or {}).get("overall") or {}).get("middle", "")
    if tail and len(text) + len(tail) + 2 <= limit - 5:
        text += "\n\n" + tail
    return text[:limit]


def alert_message(hits, limit=200):
    """조건 알림 카톡 본문."""
    text = "⚡ 조건 알림\n" + "\n".join(h["text"] for h in hits)
    return text[:limit]
