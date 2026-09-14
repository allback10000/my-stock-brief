# 주식 카톡 브리핑

등록한 종목을 하루 세 번 정기 브리핑으로, 조건이 걸리면 그때그때 카카오톡으로 보낸다.
카톡에는 200자 요약만 오고, 버튼을 누르면 전체 브리핑 페이지가 열린다.

## 무엇이 언제 오나

**정기 브리핑** (평일)

| 시각 | 내용 |
|---|---|
| 07:30 | 간밤 미국장, 오늘 한국장에서 볼 가격대 |
| 16:00 | 한국장 마감, 수급과 공시 |
| 21:00 | 미국장 개장 직전 점검 |

**조건 알림** (장중 15분 간격)

| 조건 | 기본값 | 바꾸는 곳 |
|---|---|---|
| 등락률 급변 | ±5% 이상 | `alerts.change_pct` |
| 거래량 급증 | 최근 5일 평균의 2배 | `alerts.volume_ratio` |
| 외국인·기관 수급 | 각각 50억원 이상 | `alerts.flow_krw` |
| 손절선 / 목표가 도달 | 종목별 설정값 | 종목의 `stop_loss_pct` / `take_profit_pct` |

같은 조건으로 하루 종일 울리지 않는다. `state/alerts.json`에 그날 보낸 알림을
기록해두고 건너뛴다. 급등락만 예외로 5% → 10% → 15% 구간이 바뀔 때 다시 알린다.

거래량은 장 초반에 무조건 적게 잡히므로, 경과 시간으로 하루치를 환산한 뒤
5일 평균과 비교한다. 10시에 "2배"라고 나오면 이 속도가 유지되면 종가 기준
2배가 된다는 뜻이다.

## 주가 예측을 넣지 않은 이유

"오늘 예상가"는 만들지 않았다. 차트와 뉴스로 당일 종가를 맞히는 건 되지 않는
일이고, 틀린 숫자를 매일 단정형으로 받아보면 그 숫자가 판단의 기준점이 된다.

대신 계산할 수 있는 것만 넣었다.

- **오늘 변동 예상폭** — 최근 14일 평균 변동성(ATR)을 현재가에 적용한 범위.
  "오늘 여기 안에서 움직인다"가 아니라 "최근엔 하루에 이만큼씩 움직였다"는 기록이다.
- **지지·저항 가격대** — 피벗 포인트, 20일·60일 이동평균, 20일 고가·저가.
- **손절가 / 목표가** — `watchlist.json`에 적어둔 본인 규칙을 가격으로 환산한 값.
  평단가를 넣으면 평단 기준, 없으면 현재가 기준으로 계산한다.
  AI가 정하는 게 아니라 본인이 정한 숫자라 매일 일관되게 나온다.

AI가 쓰는 오전·오후 대응도 단정형이 아니라 조건형이다.
"68,200원(20일선)이 깨지면 ~, 지키면 ~" 형태로만 쓰도록 프롬프트에 걸어뒀다.

## 세 단계 설명

브리핑 페이지 위쪽에 **쉽게 / 보통 / 자세히** 토글이 있다.

- 쉽게 — 전문용어 없이. 쓰면 바로 풀어서 설명한다
- 보통 — 이동평균선, 수급, 거래량 같은 기본 용어는 그대로 사용
- 자세히 — 밸류에이션, 매크로 연결, 수급 주체별 해석까지

내용을 줄이는 게 아니라 어휘를 바꾸는 방식이다. 세 버전이 한 페이지에 다 들어
있어서 토글은 즉시 바뀐다.

## 종목 추가와 삭제

**휴대폰에서 (권장)** — 저장소 Actions 탭 → "종목 관리" → Run workflow.
무엇을 할지(추가/삭제/목록보기)와 종목코드를 넣고 실행하면 끝이다.
종목명은 자동으로 찾아온다. 평단가와 손절·익절 기준은 선택 입력이다.

**직접 파일 수정** — `watchlist.json`을 고쳐도 된다.

```json
{
  "defaults": { "stop_loss_pct": -7, "take_profit_pct": 15 },
  "alerts": { "change_pct": 5.0, "volume_ratio": 2.0, "flow_krw": 5000000000 },
  "stocks": [
    { "code": "005930", "market": "KR", "name": "삼성전자", "avg_price": 68000 },
    { "code": "NVDA", "market": "US", "name": "엔비디아", "avg_price": null,
      "stop_loss_pct": -10, "take_profit_pct": 25 }
  ]
}
```

종목별로 `stop_loss_pct`를 따로 적으면 그 종목만 다른 기준이 적용된다.
없으면 `defaults` 값을 쓴다. 종목 수에 제한은 없지만, 카톡 200자에 들어가는 건
6~7개까지다. 그보다 많으면 요약이 잘리고 나머지는 페이지에서 봐야 한다.

**로컬에서 쓸 때**

```bash
python -m src.manage add 005930 --avg 68000
python -m src.manage add NVDA --stop -10 --target 25
python -m src.manage remove 005930
python -m src.manage list
```

## 설치

1~7단계는 이전과 같다. 요약하면:

1. **카카오 개발자 설정** — 앱 생성 → REST API 키 복사 → 카카오 로그인 ON →
   Redirect URI `http://localhost:8765/callback` → 동의항목의 "카카오톡 메시지 전송"을
   이용 중 동의로 → 제품 링크 관리 → 웹 도메인에 GitHub Pages 주소 등록.
   마지막 항목을 빠뜨리면 카톡은 오는데 버튼이 안 눌린다.
2. **리프레시 토큰** — 카카오 개발자 사이트 [도구] → [REST API 테스트]에서
   카카오 로그인 인증을 하면 화면에 나온다. 파이썬이 있으면
   `python scripts/auth.py --key <REST_API_KEY>`로도 된다.
3. **GitHub** — 저장소를 Public으로 만들고 파일을 올린다.
   Settings → Pages에서 소스를 main 브랜치의 `/docs` 폴더로 지정.
4. **Secrets 등록**

| Secret | 필수 | 발급처 |
|---|---|---|
| `KAKAO_REST_API_KEY` | ✔ | 카카오 개발자 콘솔 |
| `KAKAO_REFRESH_TOKEN` | ✔ | 위 2단계 |
| `GH_PAT` | ✔ | GitHub Fine-grained PAT, 이 저장소에 Secrets: read and write |
| `ANTHROPIC_API_KEY` | AI 브리핑 | console.anthropic.com |
| `NAVER_CLIENT_ID` / `NAVER_CLIENT_SECRET` | 국내 뉴스 | developers.naver.com |
| `DART_API_KEY` | 국내 공시 | opendart.fss.or.kr |
| `SEC_USER_AGENT` | 미국 공시 | `이름 이메일` 형식 문자열 |

없는 키는 해당 항목만 빠지고 나머지는 정상 동작한다.

5. **테스트** — Actions 탭에서 "정기 브리핑" → Run workflow.

## 알아둘 것

**Actions 사용량** — 조건 알림이 장중 15분마다 돌아서 평일 하루 60회쯤 실행된다.
Public 저장소는 Actions가 무제한이라 요금은 없다. 줄이고 싶으면
`.github/workflows/watch.yml`의 `*/15`를 `*/30`으로 바꾸면 된다.

**크론은 정확하지 않다** — GitHub 무료 러너는 부하에 따라 5~15분 늦게 뜬다.
초 단위가 중요한 매매에는 맞지 않는 구조다.

**수급은 하루 늦다** — pykrx가 가져오는 KRX 확정치라 장 마감 후에 나온다.
장중 실시간 추정 수급이 필요하면 한국투자증권 KIS Open API를 붙여야 한다.
`src/flows.py`의 `kr_flows()`만 교체하면 된다.

**국내 시세는 비공식 API** — 네이버 금융 엔드포인트를 쓴다. 공짜고 빠르지만
네이버가 바꾸면 깨진다. 안정성이 필요하면 `src/quotes.py`의 `_kr_quote()`를
KIS API로 교체한다.

**미국 수급은 없다** — 외국인·기관 일별 순매수 같은 공개 데이터가 미국에는
없다. 미국 종목은 SEC 공시로 대체한다.

**저장소가 Public이다** — 무료 플랜에서 Pages를 쓰려면 그렇다. 브리핑에 비밀은
없지만 보유 종목과 평단가는 노출된다. 평단가를 넣고 싶지 않으면 `avg_price`를
`null`로 두면 손절·목표가가 현재가 기준으로 계산된다.

## 구조

```
watchlist.json          종목 목록과 알림 기준
state/alerts.json       오늘 이미 보낸 알림 기록
src/
  config.py             종목 추가·삭제
  quotes.py             시세와 일봉
  levels.py             ATR·피벗·이동평균·손절가 계산
  flows.py              외국인·기관 수급
  news.py, filings.py   뉴스와 공시
  macro.py              지수·환율·금리
  alerts.py             조건 판정과 중복 방지
  summarize.py          AI 브리핑 (3단계 + 대응 시나리오)
  render.py             HTML과 카톡 본문
  main.py               정기 브리핑
  watch.py              조건 감시
  notify.py             카톡 발송
  manage.py             종목 관리 CLI
```
