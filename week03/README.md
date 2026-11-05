# 3주차 · 해외상품·거래소 전략 구현 — 미싱링커

**제출일: 2026/11/06(금) 23:59까지**

> 수치는 모두 `results/`의 원본 파일에서 읽은 값. 환경 구분: 모의매매는 **NH 해외 모의계좌 주문**, 백테스트는 **프로그램 내부 시뮬레이션**. 시뮬레이션 체결을 모의계좌 체결로 표기하지 않음.
> 작성 상태: `TODO`로 표시한 항목은 작성자가 직접 채울 부분.

| 항목 | 내용 |
| --- | --- |
| 팀 | 미싱링커 (Missing Linker), 07팀 — 양민수·이한용 |
| 과제 | 해외상품·거래소 전략 구현 |
| 전략 이름 | ZN 미국 10년 국채선물 이동평균 전략 (`week03_zn_treasury_futures`) |
| 대상 종목 | 미국 10년 국채선물 2026년 12월물 `ZNZ26` (CME), 거래승수 1,000, 1틱 0.015625 |
| 판단 주기 | 일봉(중기 방향) + 완성된 5분봉(장중 진입) |
| 실행 환경 | NH선물 해외 모의투자(`TRADING_ENV=mock`) · 과거 분봉 백테스트 |
| 코드 저장소 | [pioneer-1st-code-team07](https://github.com/NH-Futures-Pioneer-1-Team07/pioneer-1st-code-team07) (`week3` 브랜치, 기준 커밋 `a80cc4c`) |
| 작성일 | TODO |

## 폴더 구성

| 경로 | 내용 |
| --- | --- |
| [README.md](README.md) | 3주차 보고서 |
| [.env.example](.env.example) | 비밀값을 제외한 모의환경 설정 템플릿 (코드 저장소의 `backend/.env`로 복사해 사용) |
| [results/](results/) | 실행 원본 기록 (`meta.json`·`result.json`·`journal/`). 백테스트 7건, 모의매매 1건 |
| [screenshots/strategy/](screenshots/strategy/) | 전략 설명용 캡처 1장 |
| [screenshots/paper/](screenshots/paper/) | 모의매매 화면 캡처 13장 |
| [screenshots/backtest/](screenshots/backtest/) | 백테스트 화면 캡처 13장 |

## 1. 과제 요약

**요구사항:** NH선물 Open API로 해외 선물 상품에 대한 규칙 기반 전략을 구현하고, 실제 실행 기록으로 결과를 분석.

**한 것:**

- 미국 10년 국채선물(ZN) 단독 이동평균 전략 구현. 일봉 15·30일선으로 매매 방향을 허용하고, 5분봉 5·20 이동평균 교차로 진입.
- VIX 구간별 하루 신규 진입 한도, 증거금 대비 손익 기준 전량 청산, 중기 신호 반전 시 전량 청산 적용.
- 해외 모의계좌 주문(모의매매 1건)과 과거 분봉 백테스트(익절·손절 기준 5~50%, 7건) 실행.
- 실행 기록·화면 캡처 정리, 익절·손절 기준별 성과 비교.

**핵심 결과:** TODO (한두 문장. 예: 백테스트 7건 중 기준 30%가 순손익 +$50,038.71로 최고, 5·10·15%는 손실. 모의매매는 3계약 진입·종료 청산, 순손익 −$54.41(추정 수수료 포함))

## 2. 실행 방법

### 2-1. 사전 준비

| 항목 | 준비 내용 |
| --- | --- |
| uv | 설치(`brew install uv` 등). Python 3.12 이상은 uv가 자동 설치 |
| Node.js | 22.12 이상, npm 포함 |
| NH선물 키 | 해외 모의투자 계좌 개설 후 REST API 신청에서 **해외 모의투자용** APP Key·Secret 발급. 해외 API는 국내 키로 호출 불가 |
| VIX 데이터 | `backend/data/vixcls.csv` (FRED `VIXCLS` 일 종가). 갱신: `uv run python -m app.data.vix` |

### 2-2. 코드 내려받기

```bash
git clone --branch week3 https://github.com/NH-Futures-Pioneer-1-Team07/pioneer-1st-code-team07.git
cd pioneer-1st-code-team07
```

### 2-3. 설정

```bash
cp backend/.env.example backend/.env
```

`backend/.env`에 발급받은 키 입력. 이 제출 폴더의 [.env.example](.env.example)은 3주차 실행 항목을 정리한 템플릿.

```dotenv
TRADING_ENV=mock
NH_OVERSEAS_APP_KEY=발급받은_해외_모의투자_APP_Key
NH_OVERSEAS_APP_SECRET=발급받은_해외_모의투자_APP_Secret_Key
```

인증정보는 로컬 `backend/.env`에만 저장. 실제 값이 있는 `.env`·키·토큰·계좌 식별정보는 제출 대상에서 제외.

### 2-4. 실행

**터미널 1 — 백엔드**

```bash
cd backend
uv sync --locked
uv run uvicorn app.main:create_app --factory --reload
```

**터미널 2 — 프론트엔드**

```bash
cd frontend
npm ci
npm run dev
```

브라우저에서 [http://127.0.0.1:5173](http://127.0.0.1:5173) 접속.

### 2-5. 화면에서 실행

**백테스트 (프로그램 내부 시뮬레이션)**

- 메뉴 **백테스트**에서 전략(ZN 이동평균)·기간·초기자금·**익절·손절 기준(%)**·슬리피지를 정해 실행.
- 봉 마감 신호는 다음 봉 시가에 체결. 체결마다 슬리피지(1틱)와 수수료(0.0085%) 반영.
- 증거금·주문가능수량 제한은 미적용.
- 실행 이력에서 상세 기록 확인, 최대 4건 비교.

**모의매매 (NH 해외 모의계좌 주문)**

- 메뉴 **모의매매**에서 전략을 고르고 **운용 시작**. 운용 종료 시 미체결 취소·보유분 청산.
- 주문 접수와 체결을 구분해 확인(체결 탭).

### 2-6. 실행 기록

- 저장 위치: `backend/runs/<전략 id>/<backtest|paper>/<실행 일시>/` → 이 폴더의 `results/`로 복사.
- 복사 전 키·계좌 식별정보가 없는지 확인함 (TODO: 작성자 재확인).

## 3. 전략과 매매 계획

### 3-1. 대상 상품

| 항목 | 내용 |
| --- | --- |
| 대상 종목 | 미국 10년 국채선물 2026년 12월물 `ZNZ26` (거래소 FCME) |
| 거래승수 / 틱 | 1,000 / 0.015625 (1틱 = $15.625) |
| 증거금(매니페스트 값) | $2,083 / 계약 |
| 월물 선택 근거 | TODO |

### 3-2. 진입·청산·손절 규칙

**중기 신호 (일봉, 직전 거래일 종가 기준)**

| 신호 | 조건 | 허용 방향 |
| --- | --- | --- |
| 매수 | 종가 > 15일선 > 30일선 | 매수 |
| 매도 | 종가 < 15일선이고 < 30일선 | 매도 |
| 중립 | 그 외 | 신규 진입 없음 |

**장중 진입 (5분봉 SMA 5 / 20)**

- 매수: 단기선이 장기선을 상향 교차하고 해당 봉 종가가 두 선 위. 매도는 반대.
- 중기 신호가 허용한 방향의 신호만 진입. 교차 봉 완성 후 다음 봉에서 1계약 체결.

**하루 신규 진입 한도 (VIX 직전 거래일 종가)**

| VIX | 매수 허용일 | 매도 허용일 |
| --- | --- | --- |
| V < 15 | 1계약 | 5계약 |
| 15 ≤ V < 20 | 2계약 | 4계약 |
| 20 ≤ V < 25 | 3계약 | 3계약 |
| 25 ≤ V < 30 | 4계약 | 2계약 |
| 30 ≤ V | 5계약 | 1계약 |

**청산·손절**

| 상황 | 동작 |
| --- | --- |
| 전체 보유분의 증거금 대비 합산 손익이 ±기준(기본 20%, UI 조절)에 도달 | 전량 청산 |
| 중기 신호가 보유 방향과 반대 방향을 허용하는 신호로 바뀜 | 전량 청산 |
| 전체 보유 한도 | 전날 보유분 포함 30계약 |

전략 상세 규격: 코드 저장소 `docs/strategies/week03_zn_treasury_futures.md`.

### 3-3. 근거

TODO — 왜 국채선물인가, 왜 일봉 추세 + 5분봉 교차인가, VIX 한도의 의도(변동성에 따라 매수·매도 노출 조절), 익절·손절을 증거금 대비 비율로 둔 이유.

장중 5분봉 교차 예시 (노란 원이 단기선·장기선 교차 지점):

<figure>
  <img src="screenshots/strategy/01-intraday-5min-ma-cross-chart.png" alt="5분봉 이동평균 교차 예시" width="800">
  <figcaption><b>그림 1. 5분봉 이동평균 교차 예시</b><br>노란 원이 단기선(5봉)과 장기선(20봉)의 교차 지점. 왼쪽 원은 단기선이 장기선을 아래에서 위로 돌파하는 지점(매수 신호 형태), 오른쪽 원은 두 선이 다시 만나는 구간.</figcaption>
</figure>

## 4. 사용 API와 구조

### 4-1. 구조

```text
브라우저(React) ──REST /api · WebSocket /ws──▶ 백엔드(FastAPI) ──▶ NH선물 Open API (해외 모의)
                                                   │
                                                   ├─ 전략 코드 (backend/strategies/week03_zn_treasury_futures)
                                                   ├─ VIX 일 종가 (backend/data/vixcls.csv)
                                                   └─ 실행 기록 (backend/runs/)
```

- 모의매매와 백테스트가 같은 전략 코드를 호출. 프론트엔드는 조회와 실행 요청만 수행.

### 4-2. 사용 API

경로는 코드 저장소 `backend/app/nh/overseas/`에서 확인한 값.

| 용도 | 엔드포인트 | 사용 위치 |
| --- | --- | --- |
| 접근 토큰·웹소켓 접속키 발급 | `/v1/token`, `/v1/web-socket-key` | `nh/auth.py`, `nh/client.py` |
| 실시간 체결·호가 수신 | `/trade/ws-stream` | `nh/realtime.py` |
| 해외 분봉(5분 이력·완성 봉) | `/trade/v1/overseas/chart-minute` | `nh/overseas/quotes.py` |
| 해외 일봉(15·30일선) | `/trade/v1/overseas/chart-daily` | 〃 |
| 현재가·호가 | `/trade/v1/overseas/price`, `/bid-price` | 〃 |
| 종목 상세 | `/trade/v1/overseas/product-detail` | `nh/overseas/account.py` |
| 장 운영 시간 | `/trade/v1/overseas/market-operations` | `nh/overseas/market_hours.py` |
| 모의계좌 주문 | `/trade/v1/overseas/order` | `nh/overseas/orders.py` |
| 주문내역(체결 확인) | `/trade/v1/overseas/order-history` | `nh/overseas/account.py` |
| 예수금·잔고·주문가능수량 | `/trade/v1/overseas/deposit`, `/open-interest`, `/orderable-quantity` | `nh/overseas/account.py` |

외부 데이터: VIX 일 종가(FRED `VIXCLS`).

## 5. 실행 환경

| 구분 | 모의매매 | 백테스트 |
| --- | --- | --- |
| 성격 | **NH 해외 모의계좌 주문** | **프로그램 내부 시뮬레이션** (모의계좌 주문 없음) |
| 실행 일시 | 2026-11-04 05:43:17 ~ 19:07:46 (KST) | 2026-11-04 05:18 ~ 05:31 (KST) 실행 |
| 대상 구간 | 당일 운용 | 2026-08-11 ~ 2026-11-03 (73거래일, 5분봉 16,342개) |
| 초기 자금 | 계좌 $100,000 | $100,000 |
| 익절·손절 기준 | 30% | 5, 10, 15, 20, 30, 40, 50% (7건) |
| 비용 가정 | 수수료는 추정값(`fee_estimated`) | 수수료 0.0085%, 슬리피지 1틱(0.015625) |
| 체결 | 주문내역으로 확인한 모의계좌 체결 | 다음 봉 시가에 전량 체결 |

## 6. 실행 결과

### 6-1. 모의매매 (NH 해외 모의계좌 주문)

근거: [meta.json](results/week03_zn_treasury_futures/paper/20261104_054317/meta.json), [result.json](results/week03_zn_treasury_futures/paper/20261104_054317/result.json), [journal/](results/week03_zn_treasury_futures/paper/20261104_054317/journal/)

기록 건수(journal): 판단 148, 주문 접수 6(매수 3·매도 3), 체결 6, 거래 3.

| # | 진입 시각 | 방향 | 진입가 | 청산가 | 총손익 | 수수료(추정) | 순손익 | 진입 사유 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 08:35:04 | 매수 1계약 | 106.5 | 106.6875 | +$187.50 | $18.12 | +$169.38 | 중기 매수 허용 · 단기선 상향 교차 |
| 2 | 13:10:06 | 매수 1계약 | 106.90625 | 106.6875 | −$218.75 | $18.16 | −$236.91 | 〃 |
| 3 | 15:35:05 | 매수 1계약 | 106.65625 | 106.6875 | +$31.25 | $18.13 | +$13.12 | 〃 |

청산은 3건 모두 19:07 **운용 종료 청산**(시장가). 합계: 총손익 $0.00, 수수료 $54.41(추정), 순손익 −$54.41.
계좌 조회: 운용 후 총자산 $99,952.00, 수수료 $48.00 (`result.json`의 `account`).

<figure>
  <img src="screenshots/paper/01-dashboard-overview.png" alt="모의매매 전체 화면" width="900">
  <figcaption><b>그림 2. 모의매매 전체 화면</b><br>상단 계좌 요약, 좌측 전략 운용 패널, 가운데 일봉 차트, 우측 5호가로 구성. 운용 중 상태에서 현재가 106.66, 평가손익 −$93.75.</figcaption>
</figure>

<figure>
  <img src="screenshots/paper/02-account-summary.png" alt="계좌 요약" width="900">
  <figcaption><b>그림 3. 계좌 요약</b><br>예탁자산 $99,882.25, 예탁현금 $100,000.00, 주문 가능 금액 $93,694.25, 사용 증거금 $6,188.00. 예탁자산은 현금에 평가손익을 더한 값.</figcaption>
</figure>

<figure>
  <img src="screenshots/paper/03-strategy-run-panel.png" alt="전략 운용 패널" width="320">
  <figcaption><b>그림 4. 전략 운용 패널</b><br>ZN 미국 10년 국채선물 이동평균 전략(ZNZ26) 운용 중. 평가손익 −$93.75, 실현손익 $0.00, 추정 비용 $27.21. 하단 버튼으로 운용 종료.</figcaption>
</figure>

<figure>
  <img src="screenshots/paper/04-daily-chart-15-30-ma.png" alt="일봉 차트 (중기 신호)" width="800">
  <figcaption><b>그림 5. 일봉 차트 (중기 신호)</b><br>직전 거래일 종가 106.5(흰 점선), 15일선 106, 30일선 105.28. 종가가 두 이동평균 위에 있고 15일선이 30일선보다 높아 매수만 허용하는 상태.</figcaption>
</figure>

<figure>
  <img src="screenshots/paper/05-5min-chart-5-20-ma.png" alt="5분봉 차트 (장중 신호)" width="800">
  <figcaption><b>그림 6. 5분봉 차트 (장중 신호)</b><br>단기선(5봉) 106.67, 장기선(20봉) 106.68. 두 선이 맞닿은 구간으로 새 교차 신호가 없는 상태. 시간축은 08:20~18:15.</figcaption>
</figure>

<figure>
  <img src="screenshots/paper/06-current-judgment.png" alt="현재 판단 패널" width="900">
  <figcaption><b>그림 7. 현재 판단 패널</b><br>중기 판단: 매수 허용. 장중 판단: 단기선이 장기선 아래, 진입 신호 없음. VIX 21.15(20~25 구간)라 하루 신규 진입 한도 3계약 중 3계약 사용, 보유 매수 3계약, 증거금 대비 손익 +0.0%(기준 ±30%).</figcaption>
</figure>

<figure>
  <img src="screenshots/paper/07-open-position.png" alt="보유 포지션" width="620">
  <figcaption><b>그림 8. 보유 포지션</b><br>매수 3계약, 평균 진입가 106.69, 현재가 106.67, 평가손익 −$46.86.</figcaption>
</figure>

<figure>
  <img src="screenshots/paper/08-run-history-list.png" alt="모의매매 이력" width="800">
  <figcaption><b>그림 9. 모의매매 이력</b><br>3번 실행 기록: 익절·손절 기준 30%, 시작 2026.11.04 05:43:17, 종료 시각 없음(운용 중). 이력은 실시간 연결 상태로 갱신.</figcaption>
</figure>

<figure>
  <img src="screenshots/paper/09-fills-tab.png" alt="체결 탭" width="800">
  <figcaption><b>그림 10. 체결 탭</b><br>체결 3건. 08:35:04(106.5), 13:10:06(106.91), 15:35:05(106.66)에 각 매수 1계약 체결. 사유는 모두 “중기 매수 허용 · 장중 단기선 상향 교차”. 수수료는 건당 약 $9.</figcaption>
</figure>

<figure>
  <img src="screenshots/paper/10-decisions-tab.png" alt="매매 판단 탭" width="800">
  <figcaption><b>그림 11. 매매 판단 탭</b><br>5분봉마다 기록된 판단 138건(캡처 시점). 최근 판단은 18:15까지 “진입 보류”이며 사유(교차 없음, 허용 방향과 다른 교차)를 함께 표시.</figcaption>
</figure>

<figure>
  <img src="screenshots/paper/11-decision-0835-buy.png" alt="판단 #22 — 08:35 매수" width="800">
  <figcaption><b>그림 12. 판단 #22 — 08:35 매수</b><br>단기선 상향 교차 봉에서 매수 1계약 판단. 앞뒤 판단(#21, #23)은 교차 없음으로 진입 보류.</figcaption>
</figure>

<figure>
  <img src="screenshots/paper/12-decision-1310-buy.png" alt="판단 #77 — 13:10 매수" width="800">
  <figcaption><b>그림 13. 판단 #77 — 13:10 매수</b><br>중기 매수 허용 상태에서 단기선 상향 교차 → 매수 1계약. 체결 탭의 2번 체결(13:10:06)에 대응.</figcaption>
</figure>

<figure>
  <img src="screenshots/paper/13-decision-1535-buy.png" alt="판단 #106 — 15:35 매수" width="800">
  <figcaption><b>그림 14. 판단 #106 — 15:35 매수</b><br>단기선 상향 교차 → 매수 1계약. 체결 탭의 3번 체결(15:35:05)에 대응.</figcaption>
</figure>

### 6-2. 백테스트 (프로그램 내부 시뮬레이션)

기간 2026-08-11 ~ 2026-11-03, 초기자금 $100,000, 슬리피지 1틱. 근거: [results/week03_zn_treasury_futures/backtest/](results/week03_zn_treasury_futures/backtest/)

| 익절·손절 기준 | 실행 일시 | 거래 수 | 승·패 | 총손익 | 수수료 | 순손익 | 수익률 | 최대 낙폭 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 5% | [052356](results/week03_zn_treasury_futures/backtest/20261104_052356/result.json) | 200 | 79·121 | −$7,328.13 | $3,615.25 | −$10,943.37 | −10.94% | $11,228.32 (11.20%) |
| 10% | [051901](results/week03_zn_treasury_futures/backtest/20261104_051901/result.json) | 199 | 107·92 | +$218.75 | $3,596.57 | −$3,377.82 | −3.38% | $7,186.78 (7.03%) |
| 15% | [051842](results/week03_zn_treasury_futures/backtest/20261104_051842/result.json) | 200 | 105·95 | +$1,031.25 | $3,614.53 | −$2,583.28 | −2.58% | $15,018.76 (14.94%) |
| 20% | [051814](results/week03_zn_treasury_futures/backtest/20261104_051814/result.json) | 200 | 111·89 | +$7,296.88 | $3,614.64 | +$3,682.24 | +3.68% | $23,819.54 (19.27%) |
| **30%** | [053010](results/week03_zn_treasury_futures/backtest/20261104_053010/result.json) | 171 | 127·44 | +$53,125.00 | $3,086.29 | **+$50,038.71** | **+50.04%** | $37,781.86 (21.27%) |
| 40% | [053103](results/week03_zn_treasury_futures/backtest/20261104_053103/result.json) | 135 | 99·36 | +$52,343.75 | $2,441.68 | +$49,902.07 | +49.90% | $48,564.03 (25.04%) |
| 50% | [053042](results/week03_zn_treasury_futures/backtest/20261104_053042/result.json) | 105 | 69·36 | +$34,859.38 | $1,895.85 | +$32,963.53 | +32.96% | $54,658.29 (29.85%) |

**실행 화면**

<figure>
  <img src="screenshots/backtest/01-result-page-take-profit-40pct.png" alt="백테스트 결과 화면 (익절·손절 기준 40%)" width="900">
  <figcaption><b>그림 15. 백테스트 결과 화면 (익절·손절 기준 40%)</b><br>2026.08.11~2026.11.03, 초기자금 $100,000 → 최종자산 $149,902.07, 순손익 +$49,902.07(+49.90%). 거래 135건(99승 36패), 최대 낙폭 $48,564.03(25.04%), 수수료 합계 $2,441.68. 노란 선은 일별 자산, 봉은 일봉과 일별 체결 건수.</figcaption>
</figure>

<figure>
  <img src="screenshots/backtest/02-test-conditions-panel.png" alt="테스트 조건 입력 패널" width="340">
  <figcaption><b>그림 16. 테스트 조건 입력 패널</b><br>전략·종목(ZNZ26)·기간·초기자금 100,000 USD·익절·손절 기준(%)을 입력. 비용 가정은 수수료 0.0085%, 슬리피지 1틱, 다음 봉 시가 전량 체결, 증거금·주문가능수량 미제한. (캡처의 시작일 2026.10.28은 입력 화면 상태이며 실제 실행 기간은 2026-08-11 ~ 2026-11-03)</figcaption>
</figure>

<figure>
  <img src="screenshots/backtest/03-result-take-profit-30pct-tooltip.png" alt="백테스트 결과 화면 (기준 30%, 일별 툴팁)" width="900">
  <figcaption><b>그림 17. 백테스트 결과 화면 (기준 30%, 일별 툴팁)</b><br>최종자산 $150,038.71, 순손익 +$50,038.71(+50.04%), 거래 171건(127승 44패), 최대 낙폭 $37,781.86(21.27%). 9월 24일에 마우스를 올리면 그날 자산 $149,434.97과 체결 내역(매도 1계약씩)과 사유를 표시.</figcaption>
</figure>

<figure>
  <img src="screenshots/backtest/04-run-history-list.png" alt="실행 이력" width="900">
  <figcaption><b>그림 18. 실행 이력</b><br>실행별 일시·익절·손절 기준·기간·초기자금·슬리피지·순손익. 40% +$49,902.07, 50% +$32,963.53, 30% +$50,038.71, 5% −$10,943.37, 10% −$3,377.82, 15% −$2,583.28, 20% +$3,682.24.</figcaption>
</figure>

<figure>
  <img src="screenshots/backtest/05-run-detail-decisions-tab.png" alt="실행 상세 기록 — 매매 판단 (30%)" width="700">
  <figcaption><b>그림 19. 실행 상세 기록 — 매매 판단 (30%)</b><br>2026.11.04 05:30:10 실행. 판단 16,342건, 체결 342건. 슬리피지는 1틱(0.015625)을 시장가 체결마다 불리한 방향으로 반영. 하단에 기간 종료 시 남은 보유분은 마지막 봉 종가로 정리한다는 안내.</figcaption>
</figure>

<figure>
  <img src="screenshots/backtest/06-run-detail-fills-tab.png" alt="실행 상세 기록 — 체결 (30%)" width="700">
  <figcaption><b>그림 20. 실행 상세 기록 — 체결 (30%)</b><br>체결 342건 목록. 2026.10.30 09:45 매도 3건은 “증거금 대비 평가손익 30.8%가 익절 기준 30%에 도달”로 청산. 그 이후 10.31~11.03에 매수 진입.</figcaption>
</figure>

<figure>
  <img src="screenshots/backtest/07-compare-select-runs.png" alt="이력 비교 — 실행 선택" width="900">
  <figcaption><b>그림 21. 이력 비교 — 실행 선택</b><br>같은 종목·초기자금·기간의 이력을 최대 4건 선택. 10%(A), 20%(B), 30%(C), 40%(D) 선택.</figcaption>
</figure>

<figure>
  <img src="screenshots/backtest/08-compare-select-metrics.png" alt="이력 비교 — 비교할 수치 선택" width="900">
  <figcaption><b>그림 22. 이력 비교 — 비교할 수치 선택</b><br>수익성(순손익·수익률 등), 위험(최대 낙폭), 거래(거래 수·승률), 비용(수수료), 곡선(수익률·낙폭·일별 손익) 항목을 골라 비교.</figcaption>
</figure>

<figure>
  <img src="screenshots/backtest/09-compare-parameters.png" alt="이력 비교 — 설정값" width="900">
  <figcaption><b>그림 23. 이력 비교 — 설정값</b><br>네 실행의 다른 설정은 익절·손절 기준(10·20·30·40%)뿐이고 슬리피지 1틱, 수수료율 0.000085, 이동평균 기간(15/30일, 5/20봉)은 모두 동일.</figcaption>
</figure>

<figure>
  <img src="screenshots/backtest/10-compare-metric-cards.png" alt="이력 비교 — 수치 카드" width="900">
  <figcaption><b>그림 24. 이력 비교 — 수치 카드</b><br>순손익 A −$3,377.82 / B +$3,682.24 / C +$50,038.71 / D +$49,902.07. 승률 A 53.77%, B 55.50%, C 74.27%, D 73.33%. 최대 낙폭 비율은 A 7.03%, B 19.27%, C 21.27%, D 25.04%, 수수료는 D가 가장 낮음($2,441.68).</figcaption>
</figure>

<figure>
  <img src="screenshots/backtest/11-compare-return-curve.png" alt="이력 비교 — 수익률 곡선" width="900">
  <figcaption><b>그림 25. 이력 비교 — 수익률 곡선</b><br>C(30%)와 D(40%)가 9월 이후 급등해 10월 6일 각각 69.12%, 86.01%에 도달(A −1.13%, B 15.74%). 10월 중순 급락 이후 두 곡선은 거의 겹쳐 약 50%로 마감.</figcaption>
</figure>

<figure>
  <img src="screenshots/backtest/12-compare-drawdown-curve.png" alt="이력 비교 — 낙폭 곡선" width="900">
  <figcaption><b>그림 26. 이력 비교 — 낙폭 곡선</b><br>10월 29일 기준 낙폭 A −6.62%, B −17.16%, C −14.72%, D −21.59%. 기준이 클수록 낙폭이 깊은 경향.</figcaption>
</figure>

<figure>
  <img src="screenshots/backtest/13-compare-daily-pnl.png" alt="이력 비교 — 일별 손익" width="900">
  <figcaption><b>그림 27. 이력 비교 — 일별 손익</b><br>일별 손익 막대. 10월 중순에 C·D의 큰 손실일이 나타남. 10월 29일에는 A −$1,038.40, B·C·D −$1,314.91.</figcaption>
</figure>

## 7. 해석과 한계

### 7-1. 손익 원인

- 모의매매: TODO (3건 모두 매수 진입. 총손익 $0.00에 수수료만큼 순손실. 운용 종료 시점 가격에 일괄 청산되어 규칙 청산이 아님)
- 백테스트: TODO (익절·손절 기준에 따른 성과 차이 해석. 확인한 사실: 기준 5→30%에서 거래 수 200→171, 승률 39.5%→74.3%로 상승, 기준 40·50%에서는 거래 수가 135·105로 줄고 최대 낙폭이 커짐)

### 7-2. 전략의 한계

TODO — 후보 항목:

- 기준값(5~50%)을 같은 기간 데이터로 비교해 고른 점 → 과적합 가능성, 구간 밖 검증 없음.
- 백테스트는 증거금·주문가능수량 제한을 적용하지 않음.
- 백테스트 진입 대부분이 매도(진입 체결 200건 중 매도 185건) — 기간 내 중기 신호 편중 여부 확인 필요.
- 모의매매는 하루 1회, 매수 3건뿐이라 통계적 의미 없음.
- 수수료는 추정값, 모의 체결은 실제 시장 체결과 다를 수 있음.

### 7-3. 예상과 다른 점

TODO

## 8. 오류 제보·개선·향후 계획

- **확인된 오류 기록:** 운용 종료 시 취소 요청 3건이 `7037 이미 처리완료된 [주문] 건 입니다.`로 거부됨. 해당 주문은 이미 체결된 청산 주문이었음 (`journal/2026-11-04.jsonl`, `level: warning`). TODO: 제보 여부 기재.
- 개선 사항: TODO
- 향후 계획: TODO
