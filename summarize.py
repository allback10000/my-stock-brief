"""Claude로 브리핑 생성.

두 가지를 만든다.
1. 중학생/고등학생/대학생 세 단계로 나눈 설명
2. 계산된 가격대를 근거로 한 오전·오후 조건부 대응 시나리오

'오늘 종가 얼마' 같은 예측은 시키지 않는다. 맞힐 수 없는 숫자를
매일 단정형으로 받아보면 그 숫자가 기준점이 되어버린다.
"""
import json
import os

import requests

API = "https://api.anthropic.com/v1/messages"
MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-5")

SLOT_FRAMING = {
    "morning": "지금은 한국시간 오전 7시 30분, 한국장 개장 전이다. 간밤 미국장과 오늘 한국장 흐름이 중심이다.",
    "close": "지금은 한국시간 오후 4시, 한국장이 막 마감했다. 오늘 결과와 수급·공시가 중심이다.",
    "evening": "지금은 한국시간 밤 9시, 미국장 개장 직전이다. 오늘 밤 미국장이 중심이다.",
}

SYSTEM = """너는 개인 투자자 한 명을 위한 주식 브리핑을 쓴다.

절대 하지 않는 것:
- 오늘 종가나 목표 주가를 숫자로 예측하지 않는다. 맞힐 수 없는 일이다.
- "사라", "팔아라", "지금이 기회다" 같은 매매 권유를 하지 않는다.
- 주어진 데이터에 없는 숫자를 지어내지 않는다.
- "변동성에 유의하세요", "시장을 주시하세요" 같은 빈 문장을 쓰지 않는다.

levels 안의 숫자는 과거 데이터에서 계산된 값이다. 설명할 때 이렇게 쓴다.
- expected_low/expected_high: 최근 평균 변동폭(ATR) 기준으로 오늘 움직일 만한 범위.
  예측이 아니라 "최근엔 하루에 이만큼씩 움직였다"는 통계다.
- ma20, ma60, pivot, r1, s1, high_20d, low_20d: 시장이 자주 반응하는 가격대.
- stop_loss, take_profit: 사용자가 직접 정해둔 규칙을 가격으로 환산한 값이다.
  네가 정한 게 아니므로 "회원님이 정하신 손절선"처럼 표현한다.

세 단계 설명은 내용을 줄이는 게 아니라 어휘와 비유를 바꾸는 것이다.
- middle(중학생): 전문용어 없이. 쓴다면 바로 풀어서 설명한다. 3~4문장.
- high(고등학생): 이동평균선, 수급, 거래량 같은 기본 용어는 그냥 쓴다. 3~4문장.
- college(대학생): 밸류에이션, 매크로 연결, 수급 주체별 해석까지. 4~5문장.

plan은 조건부 문장으로만 쓴다. "A가 되면 B, 아니면 C" 형태다.
단정형("오를 것이다")이나 지시형("매수하라")을 쓰지 않는다.

출력은 JSON만. 코드펜스나 설명 없이:
{
 "overall": {"middle":"...","high":"...","college":"..."},
 "stocks": {
   "종목코드": {
     "brief": {"middle":"...","high":"...","college":"..."},
     "plan": {"morning":"오전 대응 2~3문장","afternoon":"오후 대응 2~3문장"}
   }
 }
}"""


def build(slot, payload):
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return None

    prompt = (
        f"{SLOT_FRAMING.get(slot, '')}\n"
        "수급 금액 단위는 원이다. 국내 종목 가격은 원, 미국 종목은 달러다.\n\n"
        f"데이터:\n{json.dumps(payload, ensure_ascii=False, indent=1, default=str)}"
    )

    try:
        r = requests.post(
            API,
            headers={
                "x-api-key": key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": MODEL,
                "max_tokens": 8000,
                "system": SYSTEM,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=180,
        )
        r.raise_for_status()
        text = "".join(
            b.get("text", "") for b in r.json()["content"] if b.get("type") == "text"
        ).strip()
        text = text.removeprefix("```json").removeprefix("```").removesuffix("```")
        return json.loads(text.strip())
    except Exception as e:  # noqa: BLE001
        print(f"[warn] AI 브리핑 실패: {e}")
        return None
