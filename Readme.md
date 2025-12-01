# 2025-2 캡스톤 디자인 (1) 03분반 - 6조 최적의 전략 탐색 모델 개발 : 포켓몬 전투 환경 중심으로

본 프로젝트는 여러 알고리즘을 기반으로, 포켓몬 전투 환경 아래에서 최적의 전략을 도출하는 모델 개발 프로젝트입니다.

## 프로젝트 구조

### data/

포켓몬 배틀에 필요한 기본 데이터 저장소

- `type_chart.json`: 포켓몬 타입별 상성 정보
- `gen9/factory-sets.json`: 9세대 포켓몬 추천 스펙 및 기술 조합

### src/player/

배틀 전략을 수행하는 AI 플레이어 구현

#### mcts/

Monte Carlo Tree Search 알고리즘 기반 플레이어

- 랜덤 플레이아웃 정책을 통한 상태 평가
- UCB(Upper Confidence Bound) 기반 노드 선택
- 배틀 상태 공간 탐색으로 최적 행동 결정

#### minimax/

Minimax 알고리즘 기반 플레이어

- 게임 트리 탐색을 통한 승패 판단
- 알파-베타 가지치기로 탐색 효율 증대
- 휴리스틱 평가 함수로 상태 가치 계산

### src/sim/

배틀 시뮬레이션 핵심 엔진

#### BattleClass/

배틀 상태를 나타내는 경량화 데이터 객체

- `SimplifiedBattle.py`: 배틀 상태 관리

  - 턴 정보, 팀 정보, 활성 포켓몬 추적
  - 필드 효과, 날씨, 포켓몬 상태이상 관리
  - 배틀 클론 기능으로 시뮬레이션 환경 제공

- `SimplifiedPokemon.py`: 포켓몬 상태 표현

  - HP, 스탯, 능력치, 특성, 아이템 보유
  - 배틀 진행 중 임시 상태(volatiles) 추적
  - 상태이상, 스탯 변화, 효과 관리

- `SimplifiedMove.py`: 기술 정보 관리
  - 기술의 위력, 명중률, 우선도
  - 기술 분류(물리/특수/변화), 타입 정보
  - PP 관리 및 추가 효과 정의

#### BattleEngine/

배틀 로직을 구현하는 시뮬레이션 엔진

- `SimplifiedBattleEngine.py`: 턴 시뮬레이션 핵심

  - 플레이어/상대 행동 처리
  - 속도 계산으로 행동 순서 결정
  - 기술 명중률, 데미지 계산
  - 포켓몬 전환 및 배틀 종료 판정

- `DamageModifiers.py`: 데미지 계산 보조
  - 타입 상성 적용
  - 자속 보정(STAB) 계산
  - 능력치, 상태이상 등 수정자 적용

#### Supporting/

배틀 관련 보조 객체 및 열거형

- `PokemonType.py`: 포켓몬 타입 정의
- `PokemonStatus.py`: 상태이상 종류 (마비, 독, 화상 등)
- `PokemonWeather.py`: 날씨 효과 (맑음, 비, 구름 등)
- `PokemonField.py`: 필드 효과 (스피드 스왑, 리플렉터 등)
- `PokemonSideCondition.py`: 팀 측 조건 (스파이크, 스텔스록 등)
- `PokemonEffect.py`: 개별 효과 상태
- `PokemonMoveCategory.py`: 기술 분류 (물리/특수/변화)
- `PokemonTarget.py`: 기술 대상 선택

### src/test/

플레이어 성능 측정 및 검증 도구

#### Accuracy/

배틀 엔진 정확도 검증

- `SimulationReplay.py`: 실제 배틀 재현

  - 저장된 배틀 데이터로부터 턴 단위 재현
  - 시뮬레이션 결과와 실제 결과 비교
  - HP, 포켓몬 상태, 효과 등 오차율 계산

- `BattleDataSaver.py`: 배틀 데이터 저장 유틸
  - 턴별 입력값(선택한 행동) 저장
  - 턴별 결과값(변화된 상태) JSON 저장
  - 텍스트 리포트 생성

#### TestPlayers/

AI 플레이어 성능 측정

- `TestMctsPlayer.py`: MCTS 플레이어 자동 테스트
- `TestMctsPlayerWithUser.py`: MCTS 플레이어 대 사용자 대전
- `TestMinimaxPlayer.py`: Minimax 플레이어 자동 테스트

#### Time/

실행 시간 성능 분석

- `TestBattleEngineTime.py`: 배틀 엔진 연산 속도 측정
  - 턴 시뮬레이션 실행 시간
  - 대규모 배틀 시뮬레이션 성능 분석

## 사용 방법

### 기본 배틀 시뮬레이션

```python
from src.sim.BattleClass.SimplifiedBattle import SimplifiedBattle
from src.sim.BattleEngine.SimplifiedBattleEngine import SimplifiedBattleEngine

# poke-env Battle 객체로부터 시뮬레이션 환경 생성
battle = SimplifiedBattle(poke_env_battle)
engine = SimplifiedBattleEngine()

# 턴 시뮬레이션
result = engine.simulate_turn(
    battle,
    player_move_idx=0,
    opponent_move_idx=1,
    verbose=True
)
```

### AI 플레이어 활용

```python
from src.player.mcts.MctsPlayer import MctsPlayer

player = MctsPlayer(battle, engine, iterations=100)
best_action = player.choose_action()
```

## 기술 스택

- Python 3.8+
- poke-env: 포켓몬 쇼다운 배틀 환경
- 데이터 형식: JSON

## 주요 특징

- 경량화된 상태 표현으로 빠른 시뮬레이션
- 다양한 AI 알고리즘 구현 및 비교 가능
- 배틀 데이터 저장 및 검증 체계
- 성능 분석 도구 통합
- 모듈화된 구조로 확장 용이

## 개발 상태

배틀 시뮬레이션 엔진 및 기본 AI 구현 완료. 지속적인 최적화 및 알고리즘 개선 중.
