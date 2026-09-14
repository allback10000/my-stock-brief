"""세계 시장 흐름. AI 브리핑의 배경 맥락으로 쓴다."""

TICKERS = {
    "^KS11": "코스피",
    "^KQ11": "코스닥",
    "^GSPC": "S&P500",
    "^IXIC": "나스닥",
    "^SOX": "필라델피아 반도체",
    "^VIX": "VIX 변동성지수",
    "KRW=X": "원/달러 환율",
    "^TNX": "미 국채 10년물",
    "CL=F": "WTI 유가",
}


def snapshot():
    try:
        import yfinance as yf

        data = yf.download(
            list(TICKERS), period="5d", interval="1d",
            progress=False, auto_adjust=False, group_by="ticker",
        )
    except Exception:  # noqa: BLE001
        return []

    out = []
    for sym, label in TICKERS.items():
        try:
            closes = data[sym]["Close"].dropna()
            if len(closes) < 2:
                continue
            last, prev = float(closes.iloc[-1]), float(closes.iloc[-2])
            out.append({
                "name": label,
                "value": last,
                "change_pct": (last - prev) / prev * 100,
            })
        except Exception:  # noqa: BLE001
            continue
    return out
