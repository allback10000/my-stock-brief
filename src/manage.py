"""종목 추가·삭제·조회.

로컬에서:
  python -m src.manage add 005930 --avg 68000
  python -m src.manage add NVDA --stop -10 --target 25
  python -m src.manage remove 005930
  python -m src.manage list

GitHub Actions의 '종목 관리' 워크플로가 이걸 그대로 호출한다.
"""
import argparse
import os

from . import config, quotes


def resolve_name(code, market):
    if market == "KR":
        return quotes.kr_name(code)
    try:
        import yfinance as yf

        info = yf.Ticker(code).info
        return info.get("shortName") or info.get("longName") or code
    except Exception:  # noqa: BLE001
        return code


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("add")
    a.add_argument("code")
    a.add_argument("--market", choices=["KR", "US"])
    a.add_argument("--name")
    a.add_argument("--avg", type=float, help="평균 매수단가")
    a.add_argument("--stop", type=float, help="손절 기준 %% (예: -7)")
    a.add_argument("--target", type=float, help="목표 수익률 %% (예: 15)")

    r = sub.add_parser("remove")
    r.add_argument("code")
    r.add_argument("--market", choices=["KR", "US"])

    sub.add_parser("list")

    args = ap.parse_args()

    if args.cmd == "list":
        print(config.listing())
        return

    if args.cmd == "remove":
        print(config.remove(args.code, args.market))
        return

    code, market = config.normalize(args.code, args.market)
    name = args.name or resolve_name(code, market)
    print(config.add(
        code, market, name,
        avg_price=args.avg,
        stop_loss_pct=args.stop,
        take_profit_pct=args.target,
    ))
    print()
    print(config.listing())


if __name__ == "__main__":
    main()
