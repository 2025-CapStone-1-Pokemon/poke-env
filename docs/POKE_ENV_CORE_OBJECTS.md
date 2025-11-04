# poke-env 핵심 객체 완전 가이드

> **목적**: poke-env 라이브러리의 전체 구조를 파악하고 주요 객체들의 관계를 이해하기 위한 개요 문서

---

## 📌 목차

1. [개요](#개요)
2. [poke-env 아키텍처](#poke-env-아키텍처)
3. [핵심 클래스 관계도](#핵심-클래스-관계도)
4. [주요 객체 빠른 참조](#주요-객체-빠른-참조)
5. [데이터 흐름](#데이터-흐름)
6. [SimplifiedBattle 구현을 위한 매핑](#simplifiedbattle-구현을-위한-매핑)

---

## 개요

### poke-env란?

**poke-env**는 Pokemon Showdown과 상호작용하여 포켓몬 배틀 AI를 만들기 위한 Python 라이브러리입니다.

```python
from poke_env.player import Player
from poke_env.battle import Battle

class MyPlayer(Player):
    def choose_move(self, battle: Battle):
        # battle 객체에 모든 정보가 들어있음
        # - 내 포켓몬들 (battle.team)
        # - 상대 포켓몬들 (battle.opponent_team)
        # - 현재 활성 포켓몬 (battle.active_pokemon)
        # - 사용 가능한 기술 (battle.available_moves)
        # - 날씨, 필드 효과 등

        return self.choose_random_move(battle)
```

### 핵심 역할 분담

| 컴포넌트             | 역할                    | 우리가 구현할 것     |
| -------------------- | ----------------------- | -------------------- |
| **poke-env**         | 데이터 제공 + 상태 추적 | ❌ (라이브러리 사용) |
| **Pokemon Showdown** | 게임 서버 + 데이터 소스 | ❌ (서버 사용)       |
| **SimplifiedBattle** | 배틀 시뮬레이션 엔진    | ✅ **우리가 만듦**   |
| **MCTS**             | AI 의사결정 알고리즘    | ✅ **우리가 만듦**   |

---

## poke-env 아키텍처

### 디렉토리 구조

```
poke_env/
├── battle/                    # 배틀 관련 핵심 클래스들
│   ├── abstract_battle.py    # 배틀 기본 클래스 (1532줄)
│   ├── battle.py             # 1vs1 배틀 (318줄)
│   ├── double_battle.py      # 2vs2 더블배틀
│   ├── pokemon.py            # Pokemon 클래스 (1114줄) ⭐
│   ├── move.py               # Move 클래스 (937줄) ⭐
│   ├── pokemon_type.py       # 타입 시스템 ⭐
│   ├── effect.py             # 상태 효과 (1004줄)
│   ├── status.py             # 상태이상 (BRN, PAR 등)
│   ├── weather.py            # 날씨
│   ├── field.py              # 필드 효과
│   ├── side_condition.py     # 사이드 조건
│   ├── move_category.py      # 물리/특수/변화
│   ├── pokemon_gender.py     # 성별
│   ├── target.py             # 기술 대상
│   ├── observation.py        # 턴별 관찰 데이터
│   └── z_crystal.py          # Z크리스탈
│
├── data/                      # 게임 데이터
│   ├── __init__.py           # GenData 클래스
│   ├── gen_data.py           # 세대별 데이터 로더
│   └── ...
│
├── player/                    # 플레이어 클래스들
│   ├── player.py             # 기본 Player
│   ├── random_player.py      # 랜덤 플레이어
│   └── ...
│
├── stats.py                   # 스탯 계산 함수
└── teambuilder/              # 팀 빌더
```

---

## 핵심 클래스 관계도

### 1. 클래스 계층 구조

```
AbstractBattle (추상 클래스)
    ├── Battle (1vs1 배틀)
    └── DoubleBattle (2vs2 배틀)

Pokemon (포켓몬 객체)
    ├── 속성: species, types, stats, moves, ability, item
    ├── 상태: hp, status, boosts, effects
    └── 메서드: damage(), heal(), switch_in(), switch_out()

Move (기술 객체)
    ├── 속성: base_power, type, accuracy, category
    ├── 효과: secondary, boosts, status
    └── 메서드: use()

PokemonType (타입 열거형)
    ├── 18가지 타입: FIRE, WATER, GRASS, ...
    └── damage_multiplier() - 타입 상성 계산
```

### 2. 객체 관계도

```
Battle
  ├── team: Dict[str, Pokemon]                    # 내 팀 (최대 6마리)
  │     └── Pokemon
  │           ├── moves: Dict[str, Move]          # 기술들 (최대 4개)
  │           ├── types: Tuple[PokemonType, ...]  # 타입 (1~2개)
  │           ├── ability: str                    # 특성
  │           ├── item: str                       # 아이템
  │           ├── status: Status                  # 상태이상
  │           ├── effects: Dict[Effect, int]      # 효과들
  │           └── boosts: Dict[str, int]          # 능력치 변화
  │
  ├── opponent_team: Dict[str, Pokemon]           # 상대 팀
  ├── active_pokemon: Pokemon                     # 내 활성 포켓몬
  ├── opponent_active_pokemon: Pokemon            # 상대 활성 포켓몬
  │
  ├── available_moves: List[Move]                 # 사용 가능한 기술
  ├── available_switches: List[Pokemon]           # 교체 가능한 포켓몬
  │
  ├── weather: Dict[Weather, int]                 # 날씨 {Weather: 시작_턴}
  ├── fields: Dict[Field, int]                    # 필드 효과
  ├── side_conditions: Dict[SideCondition, int]   # 내 쪽 사이드 조건
  └── opponent_side_conditions: Dict[SideCondition, int]  # 상대 쪽
```

---

## 주요 객체 빠른 참조

### Battle 클래스

**위치**: `poke_env/battle/battle.py`

**핵심 속성**:

```python
# 팀 정보
battle.team: Dict[str, Pokemon]                    # 내 팀
battle.opponent_team: Dict[str, Pokemon]           # 상대 팀

# 활성 포켓몬
battle.active_pokemon: Pokemon                     # 내 활성 포켓몬
battle.opponent_active_pokemon: Pokemon            # 상대 활성 포켓몬

# 사용 가능한 행동
battle.available_moves: List[Move]                 # 사용 가능한 기술들
battle.available_switches: List[Pokemon]           # 교체 가능한 포켓몬들

# 배틀 상태
battle.turn: int                                   # 현재 턴
battle.weather: Dict[Weather, int]                 # 날씨
battle.fields: Dict[Field, int]                    # 필드 효과
battle.side_conditions: Dict[SideCondition, int]   # 사이드 조건
battle.finished: bool                              # 배틀 종료 여부
battle.won: bool                                   # 승리 여부

# 특수 행동 가능 여부
battle.can_mega_evolve: bool                       # 메가진화 가능
battle.can_z_move: bool                            # Z기술 가능
battle.can_dynamax: bool                           # 다이맥스 가능
battle.can_tera: bool                              # 테라스탈 가능
battle.trapped: bool                               # 교체 불가 여부
```

**핵심 메서드**:

```python
# 내부 업데이트 메서드 (자동 호출됨)
battle.parse_request(request: Dict)                # 서버 요청 파싱
battle.parse_message(split_message: List[str])     # 서버 메시지 파싱
battle.switch(pokemon_str, details, hp_status)     # 포켓몬 교체
```

**상세 문서**: `BATTLE_CLASS.md`

---

### Pokemon 클래스

**위치**: `poke_env/battle/pokemon.py` (1114줄)

**핵심 속성 - 기본 정보**:

```python
pokemon.species: str                               # 종족 (예: "pikachu")
pokemon.name: str                                  # 닉네임
pokemon.level: int                                 # 레벨 (보통 100 또는 50)
pokemon.gender: PokemonGender                      # 성별

# 타입
pokemon.types: Tuple[PokemonType, ...]            # 타입 (1~2개)
pokemon.type_1: PokemonType                        # 첫 번째 타입
pokemon.type_2: Optional[PokemonType]              # 두 번째 타입 (없으면 None)
```

**핵심 속성 - 종족값 및 스탯**:

```python
# 종족값 (고정값)
pokemon.base_stats: Dict[str, int]                 # {'hp': 35, 'atk': 55, ...}

# 실전 스탯 (계산된 값)
pokemon.stats: Dict[str, int]                      # 레벨, 노력치 등 반영된 실제 스탯

# 능력치 변화 (-6 ~ +6)
pokemon.boosts: Dict[str, int]                     # {'atk': 2, 'def': -1, ...}
```

**핵심 속성 - HP 및 상태**:

```python
# HP
pokemon.current_hp: int                            # 현재 HP
pokemon.max_hp: int                                # 최대 HP
pokemon.current_hp_fraction: float                 # HP 비율 (0.0 ~ 1.0)
pokemon.fainted: bool                              # 기절 여부

# 상태이상
pokemon.status: Status                             # BRN, PAR, SLP, FRZ, PSN, TOX
pokemon.status_counter: int                        # 상태이상 카운터 (잠듦, 맹독)
```

**핵심 속성 - 기술 및 특성**:

```python
# 기술
pokemon.moves: Dict[str, Move]                     # {'thunderbolt': Move, ...}

# 특성
pokemon.ability: str                               # 'static', 'overgrow' 등
pokemon.possible_abilities: List[str]              # 가능한 특성 목록

# 아이템
pokemon.item: str                                  # 'leftovers', 'choicescarf' 등
```

**핵심 속성 - 효과 및 상태**:

```python
# 효과 (혼란, 도발, 앵콜 등)
pokemon.effects: Dict[Effect, int]                 # {Effect.CONFUSION: 2, ...}

# 배틀 상태
pokemon.active: bool                               # 필드에 나와있는지
pokemon.first_turn: bool                           # 이번 턴에 나왔는지
pokemon.must_recharge: bool                        # 반동 필요 (파괴광선)
pokemon.protecting: bool                           # 방어 중
pokemon.protect_counter: int                       # 연속 방어 카운터
```

**핵심 메서드**:

```python
# HP 조작
pokemon.damage(hp_status: str)                     # 데미지 받음
pokemon.heal(hp_status: str)                       # 회복
pokemon.set_hp(hp_status: str)                     # HP 설정
pokemon.faint()                                    # 기절

# 능력치 변화
pokemon.boost(stat: str, amount: int)              # 능력치 상승/하락
pokemon.set_boost(stat: str, amount: int)          # 능력치 변화 설정
pokemon.clear_boosts()                             # 능력치 변화 초기화

# 상태 관리
pokemon.start_effect(effect_str: str)              # 효과 시작
pokemon.end_effect(effect_str: str)                # 효과 종료
pokemon.cure_status(status: str)                   # 상태이상 치료

# 교체
pokemon.switch_in(details: str)                    # 교체 들어옴
pokemon.switch_out()                               # 교체 나감

# 기술 사용
pokemon.moved(move_id: str, failed: bool)          # 기술 사용
pokemon.prepare(move_id: str, target: Pokemon)     # 기술 준비 (솔라빔 등)

# 타입 상성
pokemon.damage_multiplier(type_or_move)            # 타입 상성 배율
```

**상세 문서**: `POKEMON_CLASS.md`

---

### Move 클래스

**위치**: `poke_env/battle/move.py` (937줄)

**핵심 속성 - 기본 정보**:

```python
move.id: str                                       # 기술 ID ('thunderbolt')
move.base_power: int                               # 위력 (90)
move.type: PokemonType                             # 타입 (PokemonType.ELECTRIC)
move.category: MoveCategory                        # PHYSICAL/SPECIAL/STATUS
move.accuracy: float                               # 명중률 (0.0 ~ 1.0)
move.priority: int                                 # 우선도 (-7 ~ +5)
```

**핵심 속성 - PP**:

```python
move.max_pp: int                                   # 최대 PP
move.current_pp: int                               # 현재 PP
```

**핵심 속성 - 추가 효과**:

```python
# 능력치 변화
move.boosts: Dict[str, int]                        # 상대에게 주는 능력치 변화
move.self_boost: Dict[str, int]                    # 자신의 능력치 변화

# 상태이상
move.status: Status                                # 상태이상 (BRN, PAR 등)

# 추가 효과
move.secondary: List[Dict]                         # 추가 효과 리스트
move.recoil: float                                 # 반동 데미지 비율
move.drain: float                                  # 흡수 비율
move.heal: float                                   # 회복 비율

# 명중 관련
move.crit_ratio: int                               # 급소율 (0~6)
move.expected_hits: float                          # 예상 타격 횟수 (1~5)
```

**핵심 속성 - 플래그 및 특성**:

```python
move.flags: Set[str]                               # 'contact', 'protect', 'mirror' 등
move.breaks_protect: bool                          # 방어 관통 여부
move.ignore_ability: bool                          # 특성 무시
move.ignore_defensive: bool                        # 방어 랭크 무시
move.ignore_evasion: bool                          # 회피율 무시
move.ignore_immunity: bool | Set[PokemonType]      # 타입 면역 무시
```

**핵심 속성 - 대상 및 효과**:

```python
move.target: Target                                # 기술 대상
move.weather: Weather                              # 날씨 변경
move.terrain: Field                                # 필드 변경
move.side_condition: SideCondition                 # 사이드 조건 설정
move.volatile_status: Effect                       # 휘발성 상태 부여
```

**핵심 속성 - 특수 기술**:

```python
move.is_z: bool                                    # Z기술 여부
move.is_protect_move: bool                         # 방어 기술 여부
move.force_switch: bool                            # 강제 교체 (드래곤테일)
move.self_switch: bool | str                       # 자가 교체 (볼트체인지)
move.self_destruct: str                            # 자폭 (대폭발)
```

**핵심 메서드**:

```python
move.use()                                         # PP 소모
move.damage_multiplier(pokemon1, pokemon2)         # 타입 상성 배율 (deprecated)
```

**상세 문서**: `MOVE_CLASS.md`

---

### PokemonType (타입 시스템)

**위치**: `poke_env/battle/pokemon_type.py`

**열거형 값**:

```python
class PokemonType(Enum):
    BUG = auto()        # 벌레
    DARK = auto()       # 악
    DRAGON = auto()     # 드래곤
    ELECTRIC = auto()   # 전기
    FAIRY = auto()      # 페어리
    FIGHTING = auto()   # 격투
    FIRE = auto()       # 불꽃
    FLYING = auto()     # 비행
    GHOST = auto()      # 고스트
    GRASS = auto()      # 풀
    GROUND = auto()     # 땅
    ICE = auto()        # 얼음
    NORMAL = auto()     # 노말
    POISON = auto()     # 독
    PSYCHIC = auto()    # 에스퍼
    ROCK = auto()       # 바위
    STEEL = auto()      # 강철
    WATER = auto()      # 물
    STELLAR = auto()    # 스텔라 (9세대)
```

**핵심 메서드**:

```python
# 타입 상성 계산 (가장 중요!)
damage_mult = PokemonType.ELECTRIC.damage_multiplier(
    type_1=PokemonType.WATER,
    type_2=None,
    type_chart=battle._data.type_chart
)
# → 2.0 (효과가 굉장!)

# 문자열에서 타입 객체 생성
type_obj = PokemonType.from_name("Fire")  # PokemonType.FIRE
```

**상세 문서**: `SUPPORTING_CLASSES.md`

---

### Status (상태이상)

**위치**: `poke_env/battle/status.py`

**열거형 값**:

```python
class Status(Enum):
    BRN = auto()    # 화상 - 물리 공격력 절반, 매 턴 1/16 데미지
    FNT = auto()    # 기절
    FRZ = auto()    # 얼음 - 행동 불가 (20% 확률 해제)
    PAR = auto()    # 마비 - 스피드 50%, 25% 확률 행동 불가
    PSN = auto()    # 독 - 매 턴 1/8 데미지
    SLP = auto()    # 잠듦 - 1~3턴 행동 불가
    TOX = auto()    # 맹독 - 턴마다 증가하는 데미지 (1/16, 2/16, ...)
```

**사용 예**:

```python
if pokemon.status == Status.BRN:
    # 화상 상태
    physical_attack *= 0.5  # 물리 공격력 절반

if pokemon.status == Status.PAR:
    # 마비 상태
    speed *= 0.5  # 스피드 절반
```

**상세 문서**: `SUPPORTING_CLASSES.md`

---

### Effect (효과)

**위치**: `poke_env/battle/effect.py` (1004줄, 200+ 효과)

**주요 효과들**:

```python
class Effect(Enum):
    # 휘발성 상태
    CONFUSION = auto()        # 혼란
    ATTRACT = auto()          # 헤롱헤롱
    ENCORE = auto()           # 앵콜
    TAUNT = auto()            # 도발
    TORMENT = auto()          # 트집

    # 필드 효과
    LEECH_SEED = auto()       # 씨뿌리기
    SUBSTITUTE = auto()       # 대타
    AQUA_RING = auto()        # 아쿠아링
    INGRAIN = auto()          # 뿌리박기

    # 특수 상태
    PROTECT = auto()          # 방어
    ENDURE = auto()           # 버티기
    FOCUS_ENERGY = auto()     # 기합
    MINIMIZE = auto()         # 작아지기

    # 변화
    TYPECHANGE = auto()       # 타입 변경 (물기먹기 등)
    ABILITY_CHANGE = auto()   # 특성 변경
    TRANSFORM = auto()        # 변신

    # 카운터
    PERISH0 = auto()          # 멸망의노래 0턴
    PERISH1 = auto()          # 멸망의노래 1턴
    PERISH2 = auto()          # 멸망의노래 2턴
    PERISH3 = auto()          # 멸망의노래 3턴

    # ... 200+ 효과들
```

**사용 예**:

```python
# 효과 확인
if Effect.CONFUSION in pokemon.effects:
    print("혼란 상태!")

# 효과 카운터
confusion_turns = pokemon.effects[Effect.CONFUSION]
```

**상세 문서**: `SUPPORTING_CLASSES.md`

---

### Weather (날씨)

**위치**: `poke_env/battle/weather.py`

**열거형 값**:

```python
class Weather(Enum):
    RAINDANCE = auto()        # 비 - 물 1.5배, 불꽃 0.5배
    SUNNYDAY = auto()         # 맑음 - 불꽃 1.5배, 물 0.5배
    SANDSTORM = auto()        # 모래바람 - 매 턴 1/16 데미지 (바위/땅/강철 제외)
    HAIL = auto()             # 싸라기눈 - 매 턴 1/16 데미지 (얼음 제외)
    SNOW = SNOWSCAPE = auto() # 눈 (9세대)

    # 특수 날씨 (원시 그란돈/카이오가)
    DESOLATELAND = auto()     # 끝의대지 - 물 기술 무효
    PRIMORDIALSEA = auto()    # 시초의바다 - 불꽃 기술 무효
    DELTASTREAM = auto()      # 델타스트림 - 비행 타입 약점 1배
```

**사용 예**:

```python
# 날씨 확인
if Weather.RAINDANCE in battle.weather:
    # 비가 오는 중
    if move.type == PokemonType.WATER:
        damage *= 1.5
    elif move.type == PokemonType.FIRE:
        damage *= 0.5
```

**상세 문서**: `SUPPORTING_CLASSES.md`

---

### Field (필드 효과)

**위치**: `poke_env/battle/field.py`

**열거형 값**:

```python
class Field(Enum):
    # 필드 (테레인)
    ELECTRIC_TERRAIN = auto()  # 일렉트릭필드 - 전기 1.3배, 잠듦 방지
    GRASSY_TERRAIN = auto()    # 그래스필드 - 풀 1.3배, 매 턴 1/16 회복
    MISTY_TERRAIN = auto()     # 미스트필드 - 드래곤 0.5배, 상태이상 방지
    PSYCHIC_TERRAIN = auto()   # 사이코필드 - 에스퍼 1.3배, 선공기 무효

    # 룸 계열
    TRICK_ROOM = auto()        # 트릭룸 - 느린 포켓몬이 먼저 행동
    WONDER_ROOM = auto()       # 원더룸 - 방어와 특방 교체
    MAGIC_ROOM = auto()        # 매직룸 - 아이템 효과 무효

    # 기타
    GRAVITY = auto()           # 중력 - 부유 무효, 명중률 상승
```

**상세 문서**: `SUPPORTING_CLASSES.md`

---

### SideCondition (사이드 조건)

**위치**: `poke_env/battle/side_condition.py`

**주요 사이드 조건**:

```python
class SideCondition(Enum):
    # 장판 기술
    STEALTH_ROCK = auto()      # 스텔스록 - 교체 시 타입 상성 데미지
    SPIKES = auto()            # 압정뿌리기 - 교체 시 1/8 데미지 (최대 3겹)
    TOXIC_SPIKES = auto()      # 독압정 - 교체 시 독 (2겹이면 맹독)
    STICKY_WEB = auto()        # 끈적끈적네트 - 교체 시 스피드 -1

    # 방어막
    REFLECT = auto()           # 리플렉터 - 물리 데미지 절반 (5턴)
    LIGHT_SCREEN = auto()      # 빛의장막 - 특수 데미지 절반 (5턴)
    AURORA_VEIL = auto()       # 오로라베일 - 물리/특수 둘 다 절반 (싸라기눈 필요)

    # 기타
    TAILWIND = auto()          # 순풍 - 스피드 2배 (4턴)
    SAFEGUARD = auto()         # 신비의부적 - 상태이상 방지 (5턴)
    MIST = auto()              # 흰안개 - 능력치 하락 방지 (5턴)
```

**사용 예**:

```python
# 스텔스록 확인
if SideCondition.STEALTH_ROCK in battle.opponent_side_conditions:
    # 상대 쪽에 스텔스록이 깔려있음
    # 교체 시 데미지 계산 필요
    pass

# 압정뿌리기 겹수 확인
if SideCondition.SPIKES in battle.side_conditions:
    layers = battle.side_conditions[SideCondition.SPIKES]
    # layers: 1, 2, 또는 3
```

**상세 문서**: `SUPPORTING_CLASSES.md`

---

## 데이터 흐름

### 1. 배틀 시작부터 종료까지

```
1. 배틀 시작
   ↓
2. Player.choose_move(battle) 호출
   ↓
3. battle 객체 분석
   - battle.team                    # 내 팀 정보
   - battle.opponent_team           # 상대 팀 정보
   - battle.active_pokemon          # 현재 활성 포켓몬
   - battle.available_moves         # 사용 가능한 기술들
   - battle.weather                 # 날씨
   - battle.fields                  # 필드 효과
   ↓
4. 행동 선택 (기술 사용 or 교체)
   ↓
5. 서버에 전송
   ↓
6. 서버에서 배틀 진행
   ↓
7. 서버가 메시지 전송 (switch, move, damage, etc.)
   ↓
8. battle.parse_message() 자동 호출
   ↓
9. battle 객체 상태 업데이트
   - pokemon.damage()
   - pokemon.switch_in()
   - pokemon.moved()
   - battle.weather 업데이트
   ↓
10. 2번으로 돌아가기 (다음 턴)
```

### 2. Pokemon 객체 업데이트 흐름

```python
# 서버 메시지: |-damage|p2a: Pikachu|50/100
battle.parse_message(['-damage', 'p2a: Pikachu', '50/100'])
    ↓
pokemon = battle.get_pokemon('p2a: Pikachu')
pokemon.damage('50/100')
    ↓
pokemon.set_hp_status('50/100')
    ↓
pokemon._current_hp = 50
pokemon._max_hp = 100
```

### 3. Move 사용 흐름

```python
# 서버 메시지: |move|p1a: Charizard|Flamethrower|p2a: Venusaur
battle.parse_message(['move', 'p1a: Charizard', 'Flamethrower', 'p2a: Venusaur'])
    ↓
pokemon = battle.get_pokemon('p1a: Charizard')
pokemon.moved('Flamethrower')
    ↓
pokemon._add_move('flamethrower', use=True)
    ↓
if 'flamethrower' not in pokemon.moves:
    move = Move('flamethrower', gen=8)
    pokemon.moves['flamethrower'] = move
pokemon.moves['flamethrower'].use()  # PP -1
```

---

## SimplifiedBattle 구현을 위한 매핑

### poke-env → SimplifiedBattle 데이터 매핑

| poke-env 데이터          | SimplifiedBattle에서 필요한 이유 | 복사 방법          |
| ------------------------ | -------------------------------- | ------------------ |
| **Pokemon 기본**         |                                  |                    |
| `pokemon.species`        | 종족값 조회                      | 문자열 복사        |
| `pokemon.level`          | 스탯 계산                        | 정수 복사          |
| `pokemon.types`          | 타입 상성 계산                   | Tuple 복사         |
| `pokemon.base_stats`     | 데미지 계산                      | Dict 얕은 복사     |
| `pokemon.stats`          | 데미지 계산                      | Dict 얕은 복사     |
| **Pokemon HP/상태**      |                                  |                    |
| `pokemon.current_hp`     | 승패 판정, HP 관리               | 정수 복사          |
| `pokemon.max_hp`         | HP 비율 계산                     | 정수 복사          |
| `pokemon.status`         | 데미지/스피드 보정               | Enum 복사          |
| `pokemon.fainted`        | 교체 가능 여부                   | 불리언 복사        |
| **Pokemon 능력치**       |                                  |                    |
| `pokemon.boosts`         | 데미지 계산                      | Dict 얕은 복사     |
| `pokemon.ability`        | 특성 효과 적용                   | 문자열 복사        |
| `pokemon.item`           | 아이템 효과 적용                 | 문자열 복사        |
| **Pokemon 기술**         |                                  |                    |
| `pokemon.moves`          | 사용 가능한 기술들               | `copy.deepcopy()`  |
| **Pokemon 효과**         |                                  |                    |
| `pokemon.effects`        | 혼란, 도발 등                    | Dict 얕은 복사     |
| **Move 정보**            |                                  |                    |
| `move.base_power`        | 데미지 계산                      | 정수 (이미 계산됨) |
| `move.type`              | 타입 상성                        | Enum (이미 객체)   |
| `move.category`          | 물리/특수 구분                   | Enum (이미 객체)   |
| `move.accuracy`          | 명중 판정                        | 실수 (이미 계산됨) |
| `move.priority`          | 행동 순서                        | 정수 (이미 계산됨) |
| **Battle 상태**          |                                  |                    |
| `battle.weather`         | 데미지 보정                      | Dict 얕은 복사     |
| `battle.fields`          | 데미지 보정                      | Dict 얕은 복사     |
| `battle.side_conditions` | 교체 데미지                      | Dict 얕은 복사     |
| `battle.turn`            | 턴 카운터                        | 정수 복사          |

### 복사 전략

```python
import copy

class SimplifiedPokemon:
    def __init__(self, poke_env_pokemon):
        # 기본 정보 - 문자열/정수 (얕은 복사)
        self.species = poke_env_pokemon.species
        self.level = poke_env_pokemon.level

        # HP - 정수 (얕은 복사)
        self.current_hp = poke_env_pokemon.current_hp
        self.max_hp = poke_env_pokemon.max_hp

        # 타입 - Enum Tuple (얕은 복사 OK)
        self.types = poke_env_pokemon.types

        # 스탯 - Dict (얕은 복사)
        self.base_stats = poke_env_pokemon.base_stats.copy()
        self.stats = poke_env_pokemon.stats.copy()

        # 능력치 변화 - Dict (얕은 복사)
        self.boosts = poke_env_pokemon.boosts.copy()

        # 기술 - Dict of Move objects (깊은 복사 필요!)
        self.moves = copy.deepcopy(poke_env_pokemon.moves)

        # 효과 - Dict (얕은 복사)
        self.effects = poke_env_pokemon.effects.copy()

        # 상태이상 - Enum (얕은 복사)
        self.status = poke_env_pokemon.status
```

### 구현 시 주의사항

1. **Move 객체는 deepcopy 필요**

   - Move 객체 내부에 `current_pp` 같은 변경 가능한 상태가 있음
   - 시뮬레이션에서 PP를 소모하면 원본에 영향을 줌

2. **Enum 타입은 복사 불필요**

   - `PokemonType`, `Status`, `Effect` 등은 불변 객체
   - 그대로 참조해도 안전

3. **Dict는 얕은 복사로 충분**

   - `base_stats`, `boosts`, `effects` 등
   - 값이 정수이므로 `.copy()`로 충분

4. **타입 상성 계산은 poke-env 활용**
   ```python
   # SimplifiedBattle에서
   effectiveness = move.type.damage_multiplier(
       defender.types[0],
       defender.types[1] if len(defender.types) > 1 else None,
       type_chart=self._data.type_chart
   )
   ```

---

## 다음 단계

이제 각 클래스별 상세 문서를 읽어보세요:

1. **[POKEMON_CLASS.md](POKEMON_CLASS.md)** - Pokemon 클래스 완전 분석
2. **[MOVE_CLASS.md](MOVE_CLASS.md)** - Move 클래스 완전 분석
3. **[BATTLE_CLASS.md](BATTLE_CLASS.md)** - Battle 클래스 완전 분석
4. **[SUPPORTING_CLASSES.md](SUPPORTING_CLASSES.md)** - 지원 클래스들
5. **[IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md)** - SimplifiedBattle 구현 가이드

---

## 빠른 참조 - 자주 사용하는 코드

### Battle 객체에서 정보 가져오기

```python
def choose_move(self, battle: Battle):
    # 내 활성 포켓몬
    my_poke = battle.active_pokemon
    print(f"내 포켓몬: {my_poke.species}, HP: {my_poke.current_hp_fraction:.1%}")

    # 상대 활성 포켓몬
    opp_poke = battle.opponent_active_pokemon
    print(f"상대: {opp_poke.species}, HP: {opp_poke.current_hp_fraction:.1%}")

    # 사용 가능한 기술들
    for move in battle.available_moves:
        print(f"- {move.id}: 위력 {move.base_power}, 타입 {move.type.name}")

    # 교체 가능한 포켓몬들
    for poke in battle.available_switches:
        print(f"- {poke.species}: HP {poke.current_hp_fraction:.1%}")

    # 날씨 확인
    if Weather.RAINDANCE in battle.weather:
        print("비가 오는 중!")

    # 사이드 조건 확인
    if SideCondition.STEALTH_ROCK in battle.opponent_side_conditions:
        print("상대 쪽에 스텔스록!")
```

### 타입 상성 계산

```python
# Move → Pokemon 타입 상성
effectiveness = move.type.damage_multiplier(
    type_1=opponent_pokemon.type_1,
    type_2=opponent_pokemon.type_2,
    type_chart=battle._data.type_chart
)

# 또는 Pokemon 클래스 메서드 사용
effectiveness = opponent_pokemon.damage_multiplier(move)

if effectiveness >= 2.0:
    print("효과가 굉장!")
elif effectiveness <= 0.5:
    print("효과가 별로...")
elif effectiveness == 0:
    print("효과가 없다...")
```

### 능력치 변화 확인

```python
if pokemon.boosts['atk'] >= 2:
    print("공격이 크게 올랐다!")

if pokemon.boosts['spe'] < 0:
    print("스피드가 떨어졌다!")
```

### 상태 확인

```python
# 상태이상
if pokemon.status == Status.BRN:
    print("화상 상태 - 물리 공격력 절반")

if pokemon.status == Status.PAR:
    print("마비 상태 - 스피드 절반, 25% 확률 행동 불가")

# 효과
if Effect.CONFUSION in pokemon.effects:
    print("혼란 상태!")

if Effect.LEECH_SEED in pokemon.effects:
    print("씨뿌리기 중!")
```

---

**끝!** 🎯
